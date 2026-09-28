import numpy as np
import pytest

from aurora_engine.hand import compute_hand


def valley(n: int = 41, slope_along: float = 0.05, slope_across: float = 1.0) -> np.ndarray:
    """A V-shaped valley draining south: the channel runs down the middle column."""
    r, c = np.mgrid[0:n, 0:n].astype(float)
    return (n - r) * slope_along + np.abs(c - n // 2) * slope_across


def test_channel_has_zero_hand_and_sides_rise_with_distance() -> None:
    e = valley()
    outlet = np.zeros_like(e, dtype=bool)
    outlet[-1, :] = True  # the southern edge is the sea
    hand, acc = compute_hand(e, outlet, stream_cells=30)
    mid = e.shape[1] // 2
    established = acc[:, mid] >= 30  # the channel counts as drainage once it drains 30 cells
    assert established[10:].all()
    assert np.nanmax(hand[established, mid]) == pytest.approx(0.0, abs=1e-9)
    row = hand[20]
    # 5 cells across at 1 m/cell, reached diagonally 5 rows downstream at 0.05 m/row: 5.25 m
    assert row[mid + 5] == pytest.approx(5.25, abs=1e-5)
    assert row[mid + 10] > row[mid + 5]
    assert acc[-2, mid] > acc[5, mid]  # flow accumulates downstream


def test_pit_is_routed_not_trapped() -> None:
    e = valley()
    e[20, 25] -= 3.0  # a closed depression beside the channel
    outlet = np.zeros_like(e, dtype=bool)
    outlet[-1, :] = True
    hand, _ = compute_hand(e, outlet, stream_cells=30)
    assert np.isfinite(hand).all()
    assert (hand >= 0).all()


def test_permanent_water_counts_as_drainage() -> None:
    e = valley()
    outlet = np.zeros_like(e, dtype=bool)
    outlet[-1, :] = True
    water = np.zeros_like(outlet)
    water[10:15, 30:35] = True
    hand, _ = compute_hand(e, outlet, permanent_water=water, stream_cells=10_000)
    assert np.nanmax(hand[10:15, 30:35]) == pytest.approx(0.0)


def test_nodata_stays_nan_and_run_is_deterministic() -> None:
    e = valley()
    e[0, 0] = np.nan
    outlet = ~np.isfinite(e)
    outlet[-1, :] = True
    h1, _ = compute_hand(e, outlet, stream_cells=30)
    h2, _ = compute_hand(e, outlet, stream_cells=30)
    assert np.isnan(h1[0, 0])
    assert np.array_equal(h1, h2, equal_nan=True)
