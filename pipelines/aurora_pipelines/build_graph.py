"""Builds the lifeline reference data for one state region (BUILD_PLAN task 2.3; SPEC M3).

Reads the OSM network extract, district polygons, terrain and population, and writes GeoParquet
under data/ref/<state>/<build_id>/<region>/ with the BigQuery column names of ARCHITECTURE §6:
nodes, edges, facilities, substations, settlements, plus build_manifest.json.

Usage:
    python -m aurora_pipelines.build_graph --state andhra_pradesh --region godavari_krishna
"""

import argparse
import hashlib
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import yaml
from shapely.ops import unary_union

from aurora_engine.facilities import classify_pois, summary
from aurora_engine.graph import METRIC_CRS, build_graph, snap
from aurora_engine.hand import edge_hand, sample_raster
from aurora_engine.settlements import population_by_cell, settlements_from_population

ROOT = Path(__file__).resolve().parents[2]


def _latest(pattern: str) -> Path:
    found = sorted(ROOT.glob(pattern))
    if not found:
        raise FileNotFoundError(pattern)
    return found[-1]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sample_dem(lon: np.ndarray, lat: np.ndarray, dem_dir: Path) -> np.ndarray:
    """Samples Copernicus GLO-30 elevation (m) at points, tile by tile; NaN where no tile."""
    out = np.full(len(lon), np.nan)
    tiles = np.floor(lat).astype(int) * 1000 + np.floor(lon).astype(int)
    for key in np.unique(tiles):
        la, lo = divmod(int(key), 1000)
        path = dem_dir / f"Copernicus_DSM_COG_10_N{la:02d}_00_E{lo:03d}_00_DEM.tif"
        if not path.exists():
            continue
        sel = np.nonzero(tiles == key)[0]
        with rasterio.open(path) as ds:
            vals = np.fromiter(
                (v[0] for v in ds.sample(zip(lon[sel], lat[sel], strict=True))), float
            )
            if ds.nodata is not None:
                vals[vals == ds.nodata] = np.nan
        out[sel] = vals
    return out


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--state", required=True)
    ap.add_argument("--region", required=True)
    ap.add_argument("--build-id", default=datetime.now(UTC).strftime("%Y%m%d"))
    args = ap.parse_args()
    t0 = time.time()
    cfg = yaml.safe_load((ROOT / f"config/states/{args.state}.yaml").read_text())
    region_cfg = cfg["build_regions"][args.region]
    osm_dir = _latest(f"data/ref/osm/{cfg['osm_extract']}-*")
    out = ROOT / "data/ref" / args.state / args.build_id / args.region
    out.mkdir(parents=True, exist_ok=True)

    # Districts and the buffered region.
    districts_csv = pd.read_csv(ROOT / cfg["districts_csv"], dtype=str).fillna("")
    admin = gpd.read_parquet(osm_dir / "admin.parquet")
    admin = admin[admin["admin_level"] == 5].copy()
    admin["osm_relation_id"] = admin["osm_id"].astype(str)
    districts = admin[["osm_relation_id", "geometry"]].merge(
        districts_csv, on="osm_relation_id", how="inner"
    )
    region = districts[districts["name"].isin(region_cfg["districts"])]
    if len(region) != len(region_cfg["districts"]):
        raise SystemExit(f"region districts not all found: {sorted(region['name'])}")
    buffer_m = float(cfg.get("district_buffer_km", 30)) * 1000
    region_poly = unary_union(region.geometry)
    buffered = (
        gpd.GeoSeries([region_poly], crs=4326)
        .to_crs(METRIC_CRS)
        .buffer(buffer_m)
        .to_crs(4326)
        .iloc[0]
    )

    # Graph.
    net = osm_dir / args.region
    roads = gpd.read_parquet(net / "roads.parquet")
    roads = roads[roads.intersects(buffered)].reset_index(drop=True)
    waterways = gpd.read_parquet(net / "waterways.parquet")
    graph = build_graph(roads, waterways)
    labels = graph.component_labels()
    main_comp = np.bincount(labels).argmax()
    graph.nodes["component_main"] = labels == main_comp
    print(
        f"graph: {len(graph.nodes):,} nodes, {len(graph.edges):,} edges; main component "
        f"{graph.nodes['component_main'].mean():.1%} of nodes; {time.time() - t0:.0f} s"
    )

    # District of each node (for publishing results only inside a district).
    dist_join = gpd.sjoin(
        graph.nodes[["node_id", "geometry"]],
        region[["osm_relation_id", "geometry"]],
        how="left",
        predicate="within",
    )
    graph.nodes["district_lgd"] = dist_join.groupby(level=0)["osm_relation_id"].first()

    # Edge attributes: midpoint, distance to the coast, minimum elevation along the edge.
    edges = graph.edges
    mid = edges.geometry.interpolate(0.5, normalized=True)
    edges["mid_lon"], edges["mid_lat"] = mid.x.to_numpy(), mid.y.to_numpy()
    coast = gpd.read_parquet(osm_dir / "coastline.parquet")
    coast = coast[coast.intersects(buffered.buffer(1.0))].to_crs(METRIC_CRS)
    coast_union = unary_union(coast.geometry)
    edges["coast_dist_km"] = (
        gpd.GeoSeries(mid, crs=4326).to_crs(METRIC_CRS).distance(coast_union).to_numpy() / 1000
    )
    dem_dir = ROOT / "data/raw/copernicus_dem/glo30"
    coords = edges.geometry.get_coordinates(index_parts=False)
    elev = sample_dem(coords["x"].to_numpy(), coords["y"].to_numpy(), dem_dir)
    edges["min_elev_m"] = (
        pd.Series(elev, index=coords.index).groupby(level=0).min().reindex(edges.index).to_numpy()
    )
    graph.nodes["elev_m"] = sample_dem(
        graph.nodes.geometry.x.to_numpy(), graph.nodes.geometry.y.to_numpy(), dem_dir
    )
    print(
        f"edge attributes: coast distance and elevation "
        f"({np.isfinite(edges['min_elev_m']).mean():.1%} "
        f"with elevation); {time.time() - t0:.0f} s"
    )

    # Height above nearest drainage: MERIT Hydro if present, else our own 90 m HAND (hand_build).
    hand_path = next(iter(sorted((ROOT / "data/raw/merit_hydro").glob("**/*hnd*.tif"))), None)
    if hand_path is None and (out / "hand_90m.tif").exists():
        hand_path = out / "hand_90m.tif"
    if hand_path is not None:
        h = edge_hand(edges.to_crs(METRIC_CRS), hand_path)
        for k, v in h.items():
            edges[k] = v
        graph.nodes["hand_m"] = sample_raster(
            hand_path, graph.nodes.geometry.x.to_numpy(), graph.nodes.geometry.y.to_numpy()
        )
        print(f"HAND from {hand_path.relative_to(ROOT)}: edge min HAND P50 "
              f"{np.nanmedian(edges['min_hand_m']):.1f} m; {time.time() - t0:.0f} s")  # fmt: skip
    else:
        print("HAND: SKIPPED (run aurora_pipelines.hand_build first)")

    # Facilities, shelters and substations.
    pois = gpd.read_parquet(net / "pois.parquet")
    pois = pois[pois.within(buffered)]
    facilities, substations = classify_pois(pois)
    for tbl in (facilities, substations):
        s = snap(graph, tbl)
        tbl["node_id"], tbl["snap_dist_m"], tbl["unsnapped"] = (
            s["node_id"],
            s["snap_dist_m"],
            s["unsnapped"],
        )
        j = gpd.sjoin(
            tbl[["geometry"]],
            region[["osm_relation_id", "geometry"]],
            how="left",
            predicate="within",
        )
        tbl["district_lgd"] = j.groupby(level=0)["osm_relation_id"].first()
    if hand_path is not None:
        for tbl in (facilities, substations):
            tbl["hand_m"] = sample_raster(
                hand_path, tbl.geometry.x.to_numpy(), tbl.geometry.y.to_numpy()
            )
    print("facilities:\n" + summary(facilities).to_string())
    print(
        f"substations: {len(substations)}; "
        f"unsnapped facilities: {int(facilities['unsnapped'].sum())}"
    )

    # Settlements (need the WorldPop raster; skipped with a clear message if not yet downloaded).
    settlements = gpd.GeoDataFrame()
    wp = ROOT / "data/raw/worldpop/2020" / "ind_ppp_2020_ap_od.tif"
    wp_full = ROOT / "data/raw/worldpop/2020" / "ind_ppp_2020.tif"
    worldpop = wp if wp.exists() else wp_full if wp_full.exists() else None
    if worldpop is not None:
        pop = population_by_cell(worldpop, buffered)
        settlements = settlements_from_population(pop, buffered)
        s = snap(graph, settlements)
        settlements["node_id"], settlements["snap_dist_m"], settlements["unsnapped"] = (
            s["node_id"],
            s["snap_dist_m"],
            s["unsnapped"],
        )
        j = gpd.sjoin(
            settlements[["geometry"]],
            region[["osm_relation_id", "geometry"]],
            how="left",
            predicate="within",
        )
        settlements["district_lgd"] = j.groupby(level=0)["osm_relation_id"].first()
        settlements["hull"] = settlements["hull"].to_wkb()
        print(
            f"settlements: {len(settlements):,} H3 cells, "
            f"population {settlements['population'].sum():,.0f} (in region districts: "
            f"{settlements.loc[settlements.district_lgd.notna(), 'population'].sum():,.0f})"
        )
    else:
        print("settlements: SKIPPED (WorldPop raster not downloaded yet)")

    # Write.
    graph.nodes.to_parquet(out / "nodes.parquet")
    edges.to_parquet(out / "edges.parquet")
    facilities.to_parquet(out / "facilities.parquet")
    substations.to_parquet(out / "substations.parquet")
    if not settlements.empty:
        settlements.to_parquet(out / "settlements.parquet")
    region[["osm_relation_id", "name", "imd_subdivision", "geometry"]].to_parquet(
        out / "districts.parquet"
    )
    manifest: dict[str, Any] = {
        "state": args.state,
        "region": args.region,
        "build_id": args.build_id,
        "created_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "inputs": {
            "osm_extract_dir": str(osm_dir.relative_to(ROOT)),
            "worldpop": str(worldpop.relative_to(ROOT)) if worldpop else None,
            "hand": str(hand_path.relative_to(ROOT)) if hand_path else None,
        },
        "counts": {
            "nodes": len(graph.nodes),
            "edges": len(edges),
            "bridges": int((edges.crossing_type == "bridge").sum()),
            "culverts": int((edges.crossing_type == "culvert").sum()),
            "fords": int((edges.crossing_type == "ford").sum()),
            "facilities": facilities["type"].value_counts().to_dict(),
            "substations": len(substations),
            "settlements": len(settlements),
        },
        "parameters": [
            {
                "name": "district_buffer_km",
                "value": buffer_m / 1000,
                "status": "PRIOR",
                "source": "BUILD_PLAN 2.3",
            },
            {"name": "snap_max_m", "value": 2000, "status": "PRIOR", "source": "SPEC M3"},
            {"name": "culvert_half_length_m", "value": 10, "status": "PRIOR", "source": "graph.py"},
            {
                "name": "settlement_min_population",
                "value": 25,
                "status": "PRIOR",
                "source": "DATA §2",
            },
            {
                "name": "road_speeds_kmph",
                "value": "graph.SPEED_KMPH",
                "status": "PRIOR",
                "source": "graph.py",
            },
        ],
        "outputs": {p.name: _sha256(p) for p in sorted(out.glob("*.parquet"))},
    }
    (out / "build_manifest.json").write_text(json.dumps(manifest, indent=2, default=str))
    print(f"wrote {out.relative_to(ROOT)} in {time.time() - t0:.0f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
