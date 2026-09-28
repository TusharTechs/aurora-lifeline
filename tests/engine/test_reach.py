"""ENGINE §7 tests: the hand-worked 6-node graph, monotonicity, availability, determinism."""

import numpy as np
import pytest

from aurora_engine.reach import (
    bottleneck_edges,
    build_csr,
    hourly_isolated_share,
    isolation_times,
    summarise,
)

INF = np.inf
# Hand-worked graph (node 6 is disconnected). Edges: (u, v, closure hour).
EDGES = [(0, 1, 10.0), (1, 2, 5.0), (0, 3, INF), (3, 2, 8.0), (2, 4, 20.0), (4, 5, 3.0)]
U = np.array([e[0] for e in EDGES])
V = np.array([e[1] for e in EDGES])
C = np.array([e[2] for e in EDGES])
CSR7 = build_csr(U, V, 7)


def test_hand_worked_isolation_times() -> None:
    b, _ = isolation_times(CSR7, C, np.array([0]))
    # 1: direct edge closes at 10; 2: best path via 3 closes at 8; 4 inherits 8; 5 cut at 3.
    assert b.tolist() == [INF, 10.0, 8.0, INF, 8.0, 3.0, -INF]


def test_critical_edges() -> None:
    b, pred = isolation_times(CSR7, C, np.array([0]))
    crit = bottleneck_edges(pred, b, U, V)
    assert crit.tolist() == [-1, 0, 3, -1, 3, 5, -1]


def test_source_availability_binds() -> None:
    b, pred = isolation_times(CSR7, C, np.array([0]), avail=np.array([6.0]))
    assert b.tolist() == [6.0, 6.0, 6.0, 6.0, 6.0, 3.0, -INF]
    crit = bottleneck_edges(pred, b, U, V)
    assert crit[1] == -1  # the hospital's own flooding binds, not a road
    assert crit[5] == 5


def test_multiple_sources_take_the_best() -> None:
    b, _ = isolation_times(CSR7, C, np.array([0, 5]), avail=np.array([INF, 12.0]))
    assert b[4] == 8.0  # via source 0 (8) beats via source 5 (min(12, 3) = 3)
    assert b[5] == 12.0


def test_monotonicity_closing_an_edge_never_raises_b() -> None:
    rng = np.random.default_rng(7)
    n, m = 200, 600
    u = rng.integers(0, n, m)
    v = rng.integers(0, n, m)
    csr = build_csr(u, v, n)
    c = np.where(rng.random(m) < 0.3, INF, rng.uniform(0, 72, m))
    src = np.array([0, 1, 2])
    b0, _ = isolation_times(csr, c, src)
    for e in rng.choice(m, 25, replace=False):
        c2 = c.copy()
        c2[e] = min(c2[e], rng.uniform(0, 72))
        b1, _ = isolation_times(csr, c2, src)
        assert np.all(b1 <= b0)


def test_determinism() -> None:
    rng = np.random.default_rng(3)
    u, v = rng.integers(0, 500, 2000), rng.integers(0, 500, 2000)
    csr = build_csr(u, v, 500)
    c = rng.uniform(0, 72, 2000)
    r1 = isolation_times(csr, c, np.array([5, 9]))
    r2 = isolation_times(csr, c, np.array([9, 5]))
    assert np.array_equal(r1[0], r2[0])
    assert np.array_equal(r1[1], r2[1])


def test_summary_probability_windows_and_never() -> None:
    # 3 members, 3 nodes: node 0 isolated in 2 of 3; node 1 never isolated; node 2 has no route.
    b = np.array([[2.0, INF, -INF], [5.0, INF, -INF], [INF, 30.0, -INF]])
    s = summarise(b, np.ones(3), landfall_h=4.0)
    assert s.p_by_landfall[0] == pytest.approx(1 / 3)
    assert s.p_by_landfall[1] == pytest.approx(0.0)
    assert np.isnan(s.p_by_landfall[2]) and s.no_route[2]
    assert s.t10[0] == 2.0 and s.t90[0] == 5.0
    assert not s.never[0]
    assert not s.never[1]  # inf in 2 of 3 members is below the 90% rule


def test_member_weights_change_probability() -> None:
    b = np.array([[1.0], [INF]])
    assert summarise(b, np.array([3.0, 1.0]), landfall_h=2.0).p_by_landfall[0] == pytest.approx(
        0.75
    )


def test_hourly_share_is_monotone_in_time() -> None:
    b = np.array([[2.0, 7.0], [5.0, INF], [9.0, INF]])
    share = hourly_isolated_share(b, np.ones(3), np.arange(0, 12, 1.0))
    assert np.all(np.diff(share, axis=0) >= 0)
    assert share[-1, 0] == pytest.approx(1.0)
