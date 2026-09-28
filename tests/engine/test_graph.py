from itertools import pairwise

import geopandas as gpd
import pytest
from shapely.geometry import LineString, Point

from aurora_engine.graph import build_graph, plan_culvert_pieces, snap

# Roughly 0.01 degree is about 1.1 km at 16.9 N. Node ids are OSM-like.
# Way 1 (primary): 1 -> 2 -> 3, west to east. Way 2 (residential): 4 -> 2 -> 5, south to north.
# Way 3 (bridge, secondary): 3 -> 6. Way 4 (tertiary): 6 -> 7 crosses a canal at x = 82.045.
# Way 5 (service): 8 -> 9, a stray fragment far from everything else.
NODES = {
    1: (82.00, 16.90), 2: (82.01, 16.90), 3: (82.02, 16.90), 4: (82.01, 16.89), 5: (82.01, 16.91),
    6: (82.03, 16.90), 7: (82.06, 16.90), 8: (82.10, 17.00), 9: (82.101, 17.00),
}  # fmt: skip


def way(way_id: int, refs: list[int], highway: str, bridge: bool = False) -> dict[str, object]:
    return {
        "way_id": way_id, "highway": highway, "name": None, "bridge": bridge, "ford": False,
        "tunnel": False, "oneway": None, "surface": None, "maxspeed": None, "layer": None,
        "node_refs": refs, "geometry": LineString([NODES[r] for r in refs]),
    }  # fmt: skip


ROADS = gpd.GeoDataFrame(
    [
        way(1, [1, 2, 3], "primary"),
        way(2, [4, 2, 5], "residential"),
        way(3, [3, 6], "secondary", bridge=True),
        way(4, [6, 7], "tertiary"),
        way(5, [8, 9], "service"),
    ],
    crs=4326,
)
CANAL = gpd.GeoDataFrame(
    [
        {
            "way_id": 99,
            "waterway": "canal",
            "name": None,
            "geometry": LineString([(82.045, 16.88), (82.045, 16.92)]),
        }
    ],
    crs=4326,
)


def test_ways_split_at_intersections() -> None:
    g = build_graph(ROADS, CANAL.iloc[0:0])
    pairs = {tuple(sorted((u, v))) for u, v in zip(g.edges.u, g.edges.v, strict=True)}
    assert {(1, 2), (2, 3), (2, 4), (2, 5), (3, 6), (6, 7), (8, 9)} == pairs


def test_bridge_is_an_explicit_edge() -> None:
    g = build_graph(ROADS, CANAL.iloc[0:0])
    bridges = g.edges[g.edges.crossing_type == "bridge"]
    assert len(bridges) == 1
    assert {int(bridges.u.iloc[0]), int(bridges.v.iloc[0])} == {3, 6}


def test_culvert_inserted_where_road_crosses_canal() -> None:
    g = build_graph(ROADS, CANAL)
    culverts = g.edges[g.edges.crossing_type == "culvert"]
    assert len(culverts) == 1
    assert culverts.length_m.iloc[0] == pytest.approx(20.0, abs=0.5)
    # The crossed road is now three edges: 6 -> a, a -> b (culvert), b -> 7, with the same length.
    way4 = g.edges[g.edges.osm_way_id == 4]
    assert len(way4) == 3
    assert way4.length_m.sum() == pytest.approx(
        ROADS.iloc[[3]].to_crs(32644).length.iloc[0], rel=1e-3
    )
    assert (culverts.u < 0).all() and (culverts.v < 0).all()


def test_lengths_and_travel_times_are_positive() -> None:
    g = build_graph(ROADS, CANAL)
    assert (g.edges.length_m > 0).all()
    assert (g.edges.travel_time_s > 0).all()
    primary = g.edges[g.edges.osm_way_id == 1]
    assert primary.length_m.sum() == pytest.approx(
        2130, rel=0.02
    )  # 0.02 degrees of longitude at 16.9 N


def test_snap_uses_main_component_and_flags_far_points() -> None:
    g = build_graph(ROADS, CANAL)
    pts = gpd.GeoDataFrame(
        geometry=[Point(82.0101, 16.9001), Point(82.1005, 17.0), Point(83.0, 18.0)], crs=4326
    )
    s = snap(g, pts)
    assert int(s.node_id.iloc[0]) == 2
    assert int(s.node_id.iloc[1]) not in {8, 9}  # the stray fragment is not the main component
    assert bool(s.unsnapped.iloc[1])  # nearest main-component node is > 2 km away
    assert bool(s.unsnapped.iloc[2])
    assert not bool(s.unsnapped.iloc[0])


def test_crossing_near_edge_end_leaves_no_zero_length_segment() -> None:
    # Canal crosses way 4 about 10 m from node 6, where a naive split would create a 0 m piece.
    near = gpd.GeoDataFrame(
        [{"way_id": 98, "waterway": "drain", "name": None,
          "geometry": LineString([(82.03009, 16.88), (82.03009, 16.92)])}],
        crs=4326,
    )  # fmt: skip
    g = build_graph(ROADS, near)
    assert (g.edges.geom_type == "LineString").all()
    assert (g.edges.length_m >= 0.5).all()


def test_plan_culvert_pieces_cover_the_edge_without_gaps() -> None:
    for dists, length in [
        ([50.0], 100.0),
        ([3.0], 100.0),
        ([98.0], 100.0),
        ([40.0, 45.0], 100.0),
        ([5.0], 12.0),
    ]:
        pieces, _ = plan_culvert_pieces(dists, length, 1, 2, -1)
        assert pieces, (dists, length)
        assert pieces[0][0] == 1 and pieces[-1][1] == 2
        assert pieces[0][2] == 0.0 and pieces[-1][3] == length
        for p, q in pairwise(pieces):
            assert p[1] == q[0] and p[3] == q[2]  # contiguous
        assert all(p[3] - p[2] >= 0.5 for p in pieces)
        assert any(p[4] == "culvert" for p in pieces)
