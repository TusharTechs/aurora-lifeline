"""OpenStreetMap extraction with pyosmium (BSD-2) for the lifeline graph (BUILD_PLAN task 2.3).

Two passes over a Geofabrik extract:

* ``boundaries``: state (admin_level 4) and district (admin_level 5) polygons plus coastline ways,
  for the whole extract. Used to pick the demo district and to measure distance to the coast.
  Boundaries are used for clipping and aggregation only; the app never renders national or
  international boundaries (CLAUDE.md, non-negotiable 11).
* ``network``: everything the graph needs inside a bounding box: drivable roads (with bridge,
  ford and tunnel tags and full node lists), waterways (for culverts), and points of interest
  (health facilities, shelters, substations).

Outputs are GeoParquet files under data/ref/osm/<extract>/.

Usage:
    python -m aurora_pipelines.osm_extract boundaries --pbf <file.osm.pbf> --out <dir>
    python -m aurora_pipelines.osm_extract network --pbf <file> --bbox W S E N --out <dir>
"""

import argparse
import sys
import time
from pathlib import Path
from typing import Any

import geopandas as gpd
import osmium
import pandas as pd
from shapely import wkb
from shapely.geometry import LineString, Point

WKB = osmium.geom.WKBFactory()

# Drivable road classes for emergency access (OSM highway=*). Tracks and paths are excluded.
ROAD_CLASSES = {
    "motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link",
    "secondary", "secondary_link", "tertiary", "tertiary_link", "unclassified",
    "residential", "living_street", "service", "road",
}  # fmt: skip
WATERWAYS = {"river", "stream", "canal", "drain", "ditch"}
HEALTH_AMENITY = {"hospital", "clinic", "doctors"}
RELEVANT_KEYS = (
    "highway", "waterway", "amenity", "healthcare", "emergency", "social_facility", "power", "ford",
    "name",  # named buildings such as "Cyclone Shelter" carry no other relevant key
)  # fmt: skip


def _tags(obj: Any) -> dict[str, str]:
    return {t.k: t.v for t in obj.tags}


def extract_boundaries(pbf: Path, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    admin: list[dict[str, Any]] = []
    coast: list[dict[str, Any]] = []
    fp = (
        osmium.FileProcessor(str(pbf))
        .with_locations()
        .with_areas(osmium.filter.TagFilter(("boundary", "administrative")))
        .with_filter(
            osmium.filter.TagFilter(("boundary", "administrative"), ("natural", "coastline"))
        )
    )
    for raw in fp:
        obj: Any = raw  # pyosmium yields a union including Changeset; we only get OSM objects here
        tags = _tags(obj)
        if obj.is_area() and tags.get("admin_level") in {"4", "5"}:
            try:
                geom = wkb.loads(WKB.create_multipolygon(obj), hex=True)
            except RuntimeError:
                continue
            admin.append(
                {
                    "osm_type": "relation" if obj.from_way() is False else "way",
                    "osm_id": obj.orig_id(),
                    "admin_level": int(tags["admin_level"]),
                    "name": tags.get("name"),
                    "name_en": tags.get("name:en"),
                    "name_te": tags.get("name:te"),
                    "wikidata": tags.get("wikidata"),
                    "geometry": geom,
                }
            )
        elif obj.is_way() and tags.get("natural") == "coastline":
            try:
                coast.append(
                    {"way_id": obj.id, "geometry": wkb.loads(WKB.create_linestring(obj), hex=True)}
                )
            except (RuntimeError, osmium.InvalidLocationError):
                continue
    gpd.GeoDataFrame(admin, crs=4326).to_parquet(out / "admin.parquet")
    gpd.GeoDataFrame(coast, crs=4326).to_parquet(out / "coastline.parquet")
    print(f"boundaries: {len(admin)} admin areas, {len(coast)} coastline ways -> {out}")


class _NetworkHandler:
    def __init__(self, bbox: tuple[float, float, float, float]) -> None:
        self.w, self.s, self.e, self.n = bbox
        self.roads: list[dict[str, Any]] = []
        self.waterways: list[dict[str, Any]] = []
        self.pois: list[dict[str, Any]] = []

    def _inside(self, lon: float, lat: float) -> bool:
        return self.w <= lon <= self.e and self.s <= lat <= self.n

    def _is_poi(self, tags: dict[str, str]) -> bool:
        return (
            tags.get("amenity") in HEALTH_AMENITY
            or "healthcare" in tags
            or tags.get("amenity") in {"shelter", "social_facility"}
            or tags.get("emergency") in {"assembly_point", "shelter"}
            or "cyclone" in tags.get("name", "").lower()
            or tags.get("power") == "substation"
        )

    def node(self, n: Any) -> None:
        if not n.location.valid() or not self._inside(n.location.lon, n.location.lat):
            return
        tags = _tags(n)
        if tags and (self._is_poi(tags) or tags.get("ford") == "yes"):
            self.pois.append(
                {"osm_type": "node", "osm_id": n.id, "tags": tags,
                 "geometry": Point(n.location.lon, n.location.lat)}
            )  # fmt: skip

    def way(self, w: Any) -> None:
        tags = _tags(w)
        highway, waterway = tags.get("highway"), tags.get("waterway")
        poi = self._is_poi(tags)
        if highway not in ROAD_CLASSES and waterway not in WATERWAYS and not poi:
            return
        try:
            coords = [(nd.lon, nd.lat) for nd in w.nodes]
            refs = [nd.ref for nd in w.nodes]
        except osmium.InvalidLocationError:
            return
        if len(coords) < 2 or not any(self._inside(x, y) for x, y in coords):
            return
        line = LineString(coords)
        if highway in ROAD_CLASSES:
            self.roads.append(
                {
                    "way_id": w.id, "highway": highway, "name": tags.get("name"),
                    "bridge": tags.get("bridge", "no") not in {"no"},
                    "ford": tags.get("ford") == "yes",
                    "tunnel": tags.get("tunnel", "no") not in {"no"},
                    "oneway": tags.get("oneway"), "surface": tags.get("surface"),
                    "maxspeed": tags.get("maxspeed"), "layer": tags.get("layer"),
                    "node_refs": refs, "geometry": line,
                }
            )  # fmt: skip
        elif waterway in WATERWAYS:
            self.waterways.append(
                {"way_id": w.id, "waterway": waterway, "name": tags.get("name"), "geometry": line}
            )
        if poi and w.is_closed() and len(coords) >= 4:
            self.pois.append(
                {
                    "osm_type": "way",
                    "osm_id": w.id,
                    "tags": tags,
                    "geometry": line.convex_hull.centroid,
                }
            )


def extract_network(pbf: Path, bbox: tuple[float, float, float, float], out: Path) -> None:
    """Extracts roads, waterways and POIs in ``bbox``.

    Node locations are cached for every node, but a C++-side key filter means only objects with a
    relevant key ever reach Python, which keeps a full zone extract to a few minutes.
    """
    out.mkdir(parents=True, exist_ok=True)
    h = _NetworkHandler(bbox)
    fp = (
        osmium.FileProcessor(str(pbf))
        .with_locations("flex_mem")
        .with_filter(osmium.filter.KeyFilter(*RELEVANT_KEYS))
    )
    for raw in fp:
        obj: Any = raw
        if obj.is_node():
            h.node(obj)
        elif obj.is_way():
            h.way(obj)
    roads = gpd.GeoDataFrame(h.roads, crs=4326)
    roads["node_refs"] = roads["node_refs"].map(list)
    roads.to_parquet(out / "roads.parquet")
    gpd.GeoDataFrame(h.waterways, crs=4326).to_parquet(out / "waterways.parquet")
    pois = gpd.GeoDataFrame(h.pois, crs=4326)
    pois["tags"] = pois["tags"].map(lambda t: pd.Series(t).to_json())
    pois.to_parquet(out / "pois.parquet")
    print(f"network: {len(roads)} roads, {len(h.waterways)} waterways, {len(pois)} POIs -> {out}")


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("boundaries")
    b.add_argument("--pbf", type=Path, required=True)
    b.add_argument("--out", type=Path, required=True)
    n = sub.add_parser("network")
    n.add_argument("--pbf", type=Path, required=True)
    n.add_argument("--bbox", type=float, nargs=4, metavar=("W", "S", "E", "N"), required=True)
    n.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    t = time.time()
    if args.cmd == "boundaries":
        extract_boundaries(args.pbf, args.out)
    else:
        extract_network(args.pbf, tuple(args.bbox), args.out)
    print(f"done in {time.time() - t:.0f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
