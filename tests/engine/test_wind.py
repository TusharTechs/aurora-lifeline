"""ENGINE §3 wind tests: surface intensity within 2%, peak at R_m, asymmetry, R_m relation."""

import numpy as np
import pytest

from aurora_engine.wind import (
    K_SEA,
    fit_holland,
    gradient_wind,
    max_gradient_wind,
    surface_wind,
    translation_velocity,
    willoughby_rmax_km,
)

CASES = [
    # (V_sfc m/s, V_trans m/s, R_m km, lat, central pressure hPa or None)
    (26.4, 0.0, 40.0, 16.5, None),  # Montha-like SCS, no pressure (IMD forecast point)
    (26.4, 5.0, 40.0, 16.5, None),
    (45.0, 4.0, 25.0, 19.0, 960.0),  # very severe cyclone with pressure
    (18.0, 3.0, 60.0, 12.0, 998.0),  # depression-strength
]


def ring(p_lon: float, p_lat: float, rmax_km: float, n: int = 360) -> tuple[np.ndarray, np.ndarray]:
    th = np.linspace(0, 2 * np.pi, n, endpoint=False)
    dlat = rmax_km / 111.2 * np.sin(th)
    dlon = rmax_km / (111.2 * np.cos(np.radians(p_lat))) * np.cos(th)
    return p_lon + dlon, p_lat + dlat


@pytest.mark.parametrize(("vs", "vt", "rm", "lat", "pc"), CASES)
def test_k_times_max_gradient_wind_reproduces_surface_intensity(
    vs: float, vt: float, rm: float, lat: float, pc: float | None
) -> None:
    p = fit_holland(vs, 0.0, rm, lat, pc)  # V_translation = 0
    if p.b_clipped:
        pytest.skip("B was clipped; the 2% identity is not expected to hold")
    vmax, _ = max_gradient_wind(p.rmax_m, p.b, p.dp_pa, p.f)
    assert K_SEA * vmax == pytest.approx(vs, rel=0.02)


@pytest.mark.parametrize(("vs", "vt", "rm", "lat", "pc"), CASES)
def test_ring_maximum_with_translation_reproduces_surface_intensity(
    vs: float, vt: float, rm: float, lat: float, pc: float | None
) -> None:
    p = fit_holland(vs, vt, rm, lat, pc)
    if p.b_clipped:
        pytest.skip("B was clipped")
    lon, la = ring(82.0, lat, rm)
    v, _ = surface_wind(p, 82.0, lat, 0.0, vt, lon, la, over_land=False)  # moving due north
    assert v.max() == pytest.approx(vs, rel=0.02)


def test_profile_peaks_near_rmax() -> None:
    p = fit_holland(26.4, 0.0, 40.0, 16.5, None)
    _, r_peak = max_gradient_wind(p.rmax_m, p.b, p.dp_pa, p.f)
    assert r_peak == pytest.approx(p.rmax_m, rel=0.05)
    r = np.linspace(1_000, 400_000, 2000)
    vg = gradient_wind(r, p.rmax_m, p.b, p.dp_pa, p.f)
    assert r[np.argmax(vg)] == pytest.approx(p.rmax_m, rel=0.05)
    assert vg[-1] < 0.3 * vg.max()  # decays far from the centre


def test_right_side_is_stronger_for_a_northward_storm() -> None:
    p = fit_holland(26.4, 6.0, 40.0, 16.5, None)
    east, _ = surface_wind(
        p, 82.0, 16.5, 0.0, 6.0, np.array([82.0 + 40 / 106.6]), np.array([16.5]), False
    )
    west, _ = surface_wind(
        p, 82.0, 16.5, 0.0, 6.0, np.array([82.0 - 40 / 106.6]), np.array([16.5]), False
    )
    assert east[0] > west[0]


def test_land_reduction_and_gusts() -> None:
    p = fit_holland(30.0, 0.0, 30.0, 16.5, None)
    lon, lat = np.array([82.2]), np.array([16.5])
    sea, gust = surface_wind(p, 82.0, 16.5, 0.0, 0.0, lon, lat, over_land=False)
    land, _ = surface_wind(p, 82.0, 16.5, 0.0, 0.0, lon, lat, over_land=True)
    assert land[0] == pytest.approx(0.75 * sea[0])
    assert gust[0] == pytest.approx(1.4 * sea[0])


def test_willoughby_rmax() -> None:
    assert willoughby_rmax_km(30.0, 16.0) == pytest.approx(46.4 * np.exp(-0.465 + 0.2704), rel=1e-9)
    assert willoughby_rmax_km(60.0, 16.0) < willoughby_rmax_km(30.0, 16.0)


def test_translation_velocity_northward() -> None:
    lat = np.array([16.0, 16.1, 16.2])
    u, v = translation_velocity(np.array([82.0, 82.0, 82.0]), lat, np.array([0.0, 1.0, 2.0]))
    assert v[1] == pytest.approx(11119.5 / 3600, rel=0.01)
    assert abs(u[1]) < 1e-6
