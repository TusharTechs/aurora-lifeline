import numpy as np
import pytest

from aurora_engine.surge import (
    CoastIndex,
    alongshore_profile,
    build_neighbours,
    landfall_on_coast,
    member_surge,
)

# A straight north-south coast at x = 0 km (sea to the east, x > 0), 1 km cells, land to the west.
N = 60


def coast_index(elev_m: np.ndarray) -> CoastIndex:
    rows, cols = np.nonzero(np.ones((N, N), dtype=bool))
    rc = np.c_[rows, cols].astype(np.int64)
    d_km = (N - 1 - cols).astype(float)  # column N-1 touches the sea
    coast_s = np.arange(N, dtype=float)
    return CoastIndex(
        coast_xy_km=np.c_[np.zeros(N), np.arange(N, dtype=float)],
        coast_s_km=coast_s,
        cell_rc=rc,
        cell_elev_m=elev_m[rows, cols].astype(float),
        cell_d_km=d_km,
        cell_coast=rows.astype(np.int64),
        cell_seed=cols == N - 1,
        neighbours=build_neighbours(rc, (N, N)),
    )


def test_profile_peaks_at_s_peak_and_decays() -> None:
    s = np.arange(0, 200, 1.0)
    h = alongshore_profile(s, 2.0, 100.0, 20.0)
    assert h.max() == pytest.approx(2.0)
    assert s[np.argmax(h)] == 100.0
    assert h[140] == pytest.approx(2.0 * np.exp(-0.5), rel=1e-6)  # one sigma (2 R_m = 40 km) away


def test_connected_bathtub_blocks_water_behind_a_ridge() -> None:
    elev = np.full((N, N), 0.2)
    elev[:, 40] = 5.0  # a ridge parallel to the coast
    idx = coast_index(elev)
    out = member_surge(idx, 1.5, 30.0, +1.0, 20.0, np.empty((0, 2)), np.empty(0))
    depth = out.depth_m.reshape(N, N)
    assert depth[30, N - 2] > 0.5  # coastal lowland floods
    assert depth[30, 30] == 0.0  # low ground behind the ridge stays dry: not connected
    assert np.all(depth >= 0)


def test_water_level_decays_inland() -> None:
    elev = np.zeros((N, N))
    idx = coast_index(elev)
    out = member_surge(idx, 2.0, 30.0, +1.0, 20.0, np.empty((0, 2)), np.empty(0))
    depth = out.depth_m.reshape(N, N)
    row = depth[50]  # near the peak (s_peak = 50)
    assert row[N - 1] > row[N - 11] > row[N - 21]
    assert row[N - 11] == pytest.approx(row[N - 1] - 0.083 * 10, abs=1e-6)


def test_landfall_crossing_and_right_side() -> None:
    coast = np.c_[np.zeros(N), np.arange(N, dtype=float)]
    track = np.array(
        [[20.0, 10.0], [10.0, 20.0], [-10.0, 30.0]]
    )  # moving west-north-west, crossing x=0
    hit = landfall_on_coast(coast, np.arange(N, dtype=float), track)
    assert hit is not None
    step, s, sign = hit
    assert step == 2
    assert s == pytest.approx(25.0)
    assert sign == 1.0  # right of a westward-moving storm is north = increasing s


def test_onset_when_centre_within_rmax_plus_50km() -> None:
    idx = coast_index(np.zeros((N, N)))
    track = np.array([[200.0, 30.0], [100.0, 30.0], [40.0, 30.0], [0.0, 30.0]])
    out = member_surge(idx, 1.0, 30.0, 1.0, 20.0, track, np.array([0.0, 6.0, 12.0, 18.0]))
    assert out.onset_h[30] == 12.0  # 40 km <= 20 + 50
    assert np.isinf(out.onset_h).sum() == 0 or out.onset_h.min() >= 12.0
