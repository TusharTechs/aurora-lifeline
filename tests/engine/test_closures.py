import numpy as np
import pandas as pd
import pytest

from aurora_engine.closures import (
    approach_hand,
    build_edge_index,
    combine,
    rain_closure_hours,
    surge_closure_hours,
)

INF = np.inf
# 1 --a-- 2 ==bridge== 3 --b-- 4 ; edge c: 2 --c-- 5 (a second approach at node 2)
EDGES = pd.DataFrame(
    {
        "u": [1, 2, 3, 2],
        "v": [2, 3, 4, 5],
        "crossing_type": ["none", "bridge", "none", "none"],
        "road_class": ["residential", "primary", "primary", "residential"],
        "min_hand_m": [4.0, 0.0, 3.0, 6.0],
        "hand_u_end_m": [5.0, 0.0, 0.8, 2.5],  # near the u end of each edge
        "hand_v_end_m": [1.2, 0.0, 3.5, 6.0],  # near the v end of each edge
    }
)
PATCH = np.array([0, 0, 0, 1])


def test_bridge_uses_its_approaches_not_its_own_hand() -> None:
    hand = approach_hand(EDGES)
    # Node 2 approaches: a near v (1.2), c near u (2.5) -> 1.2. Node 3: b near u (0.8).
    assert hand[1] == pytest.approx(0.8)
    assert hand[0] == pytest.approx(4.0)  # ordinary edges keep their own minimum


def test_rain_threshold_includes_formation_allowance() -> None:
    idx = build_edge_index(EDGES, PATCH, 2)
    # Bridge on a primary road: 50 + (0.8 + 1.0 + 0.3) / 0.02 = 155 mm.
    assert idx.rain_threshold_mm[1] == pytest.approx(155.0)
    # Residential edge: 50 + (4.0 + 0.3 + 0.3) / 0.02 = 280 mm.
    assert idx.rain_threshold_mm[0] == pytest.approx(280.0)
    assert np.isinf(idx.rain_threshold_mm[3])  # 6 m + allowance is above h_max


def test_rain_closure_by_patch() -> None:
    idx = build_edge_index(EDGES, PATCH, 2)
    cum = np.array([[0, 60, 120, 200, 300], [0, 10, 20, 30, 40]], dtype=float)
    hours = rain_closure_hours(idx, cum)
    # a: 280 mm at hour 4; bridge: 155 mm at 3; b (primary, HAND 3.0): 265 mm at 4; c: never
    assert hours.tolist() == [4.0, 3.0, 4.0, INF]


def test_surge_closure_needs_depth_over_the_road() -> None:
    idx = build_edge_index(EDGES, PATCH, 2, surge_cell=np.array([0, 1, -1, 2]))
    depth = np.array([0.5, 1.2, 1.0])  # residential needs 0.6; primary bridge needs 1.3
    onset = np.array([10.0, 10.0, 12.0])
    assert surge_closure_hours(idx, depth, onset).tolist() == [INF, INF, INF, 12.0]


def test_combine_takes_earliest() -> None:
    assert combine(np.array([5.0, INF]), np.array([3.0, INF])).tolist() == [3.0, INF]
