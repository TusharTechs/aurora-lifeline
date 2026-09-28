"""Lifeline road graph from OSM ways (ENGINE §7 inputs; SPEC M3).

Vertices are OSM nodes where ways meet or end. Each way is split at those vertices into edges.
Bridges and fords are explicit edges (OSM usually splits bridge ways already). Where a road crosses
a waterway without a bridge or tunnel, the road is split and a short explicit ``culvert`` edge is
inserted at the crossing, so closures can act on the crossing itself. Roads are undirected for
emergency access. Lengths are measured in a metric projection; travel times use per-class speeds
(PRIOR).
"""

from collections import Counter
from dataclasses import dataclass

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree
from shapely import STRtree, get_coordinates, line_locate_point, points
from shapely.geometry import LineString
from shapely.ops import substring

METRIC_CRS = "EPSG:32644"  # UTM 44N covers the Andhra Pradesh and Odisha coasts

# Free-flow speeds by OSM highway class, km/h (PRIOR; only used for t0 travel times).
SPEED_KMPH = {
    "motorway": 80,
    "motorway_link": 50,
    "trunk": 60,
    "trunk_link": 40,
    "primary": 50,
    "primary_link": 35,
    "secondary": 40,
    "secondary_link": 30,
    "tertiary": 30,
    "tertiary_link": 25,
    "unclassified": 20,
    "road": 20,
    "residential": 20,
    "living_street": 10,
    "service": 10,
}
CULVERT_HALF_LENGTH_M = 10.0  # the explicit culvert edge spans +/- 10 m around the crossing (PRIOR)
MIN_SEGMENT_M = 0.5
SNAP_MAX_M = 2000.0  # SPEC M3: facilities and settlements snap within 2 km or are flagged


@dataclass
class Graph:
    """Nodes and undirected edges in long tables, plus the metric CRS they were measured in."""

    nodes: gpd.GeoDataFrame  # node_id, geometry (EPSG:4326), x, y (metric)
    edges: gpd.GeoDataFrame  # edge_id, u, v, osm_way_id, road_class, crossing_type, length_m, ...

    def component_labels(self) -> np.ndarray:
        idx = pd.Index(self.nodes["node_id"])
        u = idx.get_indexer(self.edges["u"])
        v = idx.get_indexer(self.edges["v"])
        n = len(idx)
        adj = csr_matrix((np.ones(len(u)), (u, v)), shape=(n, n))
        _, labels = connected_components(adj, directed=False)
        return np.asarray(labels)


def _vertex_refs(roads: pd.DataFrame) -> set[int]:
    counts: Counter[int] = Counter()
    ends: set[int] = set()
    for refs in roads["node_refs"]:
        counts.update(refs)
        ends.add(int(refs[0]))
        ends.add(int(refs[-1]))
    return ends | {n for n, c in counts.items() if c > 1}


def build_graph(roads: gpd.GeoDataFrame, waterways: gpd.GeoDataFrame) -> Graph:
    """Builds the undirected lifeline road graph. ``roads`` comes from osm_extract (EPSG:4326)."""
    roads = roads.reset_index(drop=True)
    vertices = _vertex_refs(roads)
    coords_by_node: dict[int, tuple[float, float]] = {}
    rows: list[dict[str, object]] = []
    for way in roads.itertuples(index=False):
        refs = [int(r) for r in way.node_refs]
        xy = get_coordinates(way.geometry)
        for r, (x, y) in zip(refs, xy, strict=True):
            coords_by_node.setdefault(r, (float(x), float(y)))
        start = 0
        for i in range(1, len(refs)):
            if refs[i] in vertices or i == len(refs) - 1:
                if refs[start] != refs[i] or i - start > 1:
                    crossing = "ford" if way.ford else "bridge" if way.bridge else "none"
                    rows.append(
                        {
                            "u": refs[start],
                            "v": refs[i],
                            "osm_way_id": int(way.way_id),
                            "road_class": way.highway,
                            "crossing_type": crossing,
                            "tunnel": bool(way.tunnel),
                            "geometry": LineString(xy[start : i + 1]),
                        }
                    )
                start = i
    edges = gpd.GeoDataFrame(rows, crs=4326)
    edges = _insert_culverts(edges, waterways, coords_by_node)
    nodes = gpd.GeoDataFrame(
        {"node_id": list(coords_by_node)},
        geometry=points(np.array(list(coords_by_node.values()))),
        crs=4326,
    )
    used = pd.unique(pd.concat([edges["u"], edges["v"]]))
    nodes = nodes[nodes["node_id"].isin(used)].reset_index(drop=True)
    metric = nodes.to_crs(METRIC_CRS)
    nodes["x"], nodes["y"] = metric.geometry.x.to_numpy(), metric.geometry.y.to_numpy()
    edges["length_m"] = edges.to_crs(METRIC_CRS).length.to_numpy()
    speed = edges["road_class"].map(SPEED_KMPH).fillna(20).to_numpy() / 3.6
    edges["travel_time_s"] = edges["length_m"].to_numpy() / speed
    edges.insert(0, "edge_id", np.arange(len(edges), dtype=np.int64))
    return Graph(nodes=nodes, edges=edges)


Piece = tuple[int, int, float, float, str]


def plan_culvert_pieces(
    dists: list[float], length: float, start_node: int, end_node: int, next_id: int
) -> tuple[list[Piece], int]:
    """Plans how an edge of ``length`` metres is split around waterway crossings at ``dists``.

    Each crossing gets a culvert spanning +/- CULVERT_HALF_LENGTH_M. Near an end of the edge, or
    the previous culvert, the culvert attaches to the existing node instead of leaving a piece
    shorter than MIN_SEGMENT_M. New nodes get negative ids starting at ``next_id``. Returns the
    pieces (u, v, from_m, to_m, kind) and the next free id; no pieces if nothing can be split.
    """
    if start_node == end_node or length < 2 * MIN_SEGMENT_M:
        return [], next_id
    pieces: list[Piece] = []
    prev_node, prev_d = start_node, 0.0
    for d in sorted({round(x, 1) for x in dists}):
        a = max(d - CULVERT_HALF_LENGTH_M, prev_d)
        b = min(d + CULVERT_HALF_LENGTH_M, length)
        if b - a < MIN_SEGMENT_M or prev_node == end_node:
            continue
        if a - prev_d >= MIN_SEGMENT_M:
            na, next_id = next_id, next_id - 1
            pieces.append((prev_node, na, prev_d, a, "none"))
        else:
            na, a = prev_node, prev_d
        if length - b >= MIN_SEGMENT_M:
            nb, next_id = next_id, next_id - 1
        else:
            nb, b = end_node, length
        pieces.append((na, nb, a, b, "culvert"))
        prev_node, prev_d = nb, b
    if not pieces:
        return [], next_id
    if prev_node != end_node:
        pieces.append((prev_node, end_node, prev_d, length, "none"))
    return pieces, next_id


def _insert_culverts(
    edges: gpd.GeoDataFrame,
    waterways: gpd.GeoDataFrame,
    coords_by_node: dict[int, tuple[float, float]],
) -> gpd.GeoDataFrame:
    """Splits plain road edges where they cross a waterway and inserts explicit culvert edges."""
    if waterways.empty:
        return edges
    plain = edges[(edges["crossing_type"] == "none") & ~edges["tunnel"]]
    tree = STRtree(waterways.geometry.to_numpy())
    hits = tree.query(plain.geometry.to_numpy(), predicate="crosses")
    if hits.size == 0:
        return edges
    metric_edges = plain.to_crs(METRIC_CRS)
    metric_water = waterways.to_crs(METRIC_CRS).geometry.to_numpy()
    crossings: dict[int, list[float]] = {}
    for e_pos, w_pos in zip(hits[0], hits[1], strict=True):
        line = metric_edges.geometry.iloc[e_pos]
        inter = line.intersection(metric_water[w_pos])
        for p in getattr(inter, "geoms", [inter]):
            if p.geom_type == "Point":
                crossings.setdefault(int(plain.index[e_pos]), []).append(
                    float(line_locate_point(line, p))
                )
    next_id = -1
    new_rows: list[dict[str, object]] = []
    drop: list[int] = []
    for idx, dists in crossings.items():
        row = edges.loc[idx]
        attrs = row.drop(labels=["geometry"]).to_dict()
        line_m = metric_edges.loc[idx, "geometry"]
        length = float(line_m.length)
        start_node, end_node = int(row["u"]), int(row["v"])
        pieces, next_id = plan_culvert_pieces(dists, length, start_node, end_node, next_id)
        if not pieces:
            continue
        drop.append(idx)
        for u, v, s_, t_, kind in pieces:
            for n, dd in ((u, s_), (v, t_)):
                if n < 0 and n not in coords_by_node:
                    pt = (
                        gpd.GeoSeries([line_m.interpolate(dd)], crs=METRIC_CRS).to_crs(4326).iloc[0]
                    )
                    coords_by_node[n] = (float(pt.x), float(pt.y))
            seg = gpd.GeoSeries([substring(line_m, s_, t_)], crs=METRIC_CRS).to_crs(4326).iloc[0]
            new_rows.append({**attrs, "u": u, "v": v, "crossing_type": kind, "geometry": seg})
    if not new_rows:
        return edges
    out = pd.concat(
        [edges.drop(index=drop), gpd.GeoDataFrame(new_rows, crs=4326)], ignore_index=True
    )
    return gpd.GeoDataFrame(out, crs=4326)


def snap(graph: Graph, points_gdf: gpd.GeoDataFrame, max_m: float = SNAP_MAX_M) -> pd.DataFrame:
    """Snaps points to the nearest node of the largest connected component.

    Returns ``node_id``, ``snap_dist_m`` and ``unsnapped`` (distance over ``max_m``) per point.
    Snapping to the main component avoids attaching a PHC to a stray, disconnected service road,
    which would otherwise read as "no mapped route".
    """
    labels = graph.component_labels()
    main = np.bincount(labels).argmax()
    keep = labels == main
    xy = np.c_[graph.nodes["x"].to_numpy()[keep], graph.nodes["y"].to_numpy()[keep]]
    ids = graph.nodes["node_id"].to_numpy()[keep]
    pm = points_gdf.to_crs(METRIC_CRS)
    dist, pos = cKDTree(xy).query(np.c_[pm.geometry.x, pm.geometry.y])
    return pd.DataFrame(
        {"node_id": ids[pos], "snap_dist_m": dist, "unsnapped": dist > max_m},
        index=points_gdf.index,
    )
