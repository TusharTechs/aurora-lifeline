"""Parametric wind field: Holland (1980) gradient wind reduced to the surface (ENGINE §3).

Implemented from the published equations; CLIMADA (GPL) is not used. Units are SI throughout:
radius in metres, pressure deficit in pascals, winds in m/s.

    V_g(r) = sqrt( (B/rho) (Rm/r)^B dp exp(-(Rm/r)^B) + (r f / 2)^2 ) - r f / 2

* V_mg, the maximum gradient-level wind, comes from the surface intensity:
  V_mg = (V_sfc - 0.5 V_translation) / K, with K = 0.8 over sea (PRIOR).
* If the central pressure is known, B is solved (unclipped) so that max_r V_g = V_mg, starting from
  Holland's B = rho e V_mg^2 / dp, then clipped to [1.0, 2.5]. If it is missing (typical for IMD
  forecast points), B = 1.5 (PRIOR) and dp is solved instead.
* Surface wind V_s = K V_g, times a land reduction factor of 0.75 over land (PRIOR), plus
  0.5 x the translation velocity projected on the local wind direction (inflow angle 20 deg, PRIOR).
  Gusts are 1.4 x the sustained wind (PRIOR).
"""

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.optimize import brentq, minimize_scalar

RHO_AIR = 1.15  # kg/m^3
OMEGA = 7.2921e-5  # rad/s
K_SEA = 0.8  # gradient-to-surface reduction over sea (PRIOR)
LAND_FACTOR = 0.75  # additional reduction over land (PRIOR)
INFLOW_DEG = 20.0  # (PRIOR)
GUST_FACTOR = 1.4  # (PRIOR)
B_DEFAULT = 1.5  # when central pressure is missing (PRIOR)
B_CLIP = (1.0, 2.5)
EARTH_RADIUS_M = 6_371_008.8


def coriolis(lat_deg: float) -> float:
    return float(2 * OMEGA * np.sin(np.radians(abs(lat_deg))))


def willoughby_rmax_km(vmax_ms: float, lat_deg: float) -> float:
    """R_m (Willoughby et al., 2006): 46.4 exp(-0.0155 Vmax + 0.0169 |lat|) km; Vmax in m/s."""
    return float(46.4 * np.exp(-0.0155 * vmax_ms + 0.0169 * abs(lat_deg)))


def gradient_wind(
    r_m: ArrayLike, rmax_m: float, b: float, dp_pa: float, f: float
) -> NDArray[np.float64]:
    """Holland (1980) gradient wind (m/s) at radius ``r_m``."""
    r = np.maximum(np.asarray(r_m, dtype=np.float64), 1.0)
    x = (rmax_m / r) ** b
    return np.asarray(np.sqrt(b / RHO_AIR * x * dp_pa * np.exp(-x) + (r * f / 2) ** 2) - r * f / 2)


def max_gradient_wind(rmax_m: float, b: float, dp_pa: float, f: float) -> tuple[float, float]:
    """(max_r V_g, radius of that maximum), including the Coriolis term."""
    res = minimize_scalar(
        lambda r: -float(gradient_wind(r, rmax_m, b, dp_pa, f)),
        bounds=(0.3 * rmax_m, 3.0 * rmax_m),
        method="bounded",
        options={"xatol": 1.0},
    )
    return float(-res.fun), float(res.x)


@dataclass(frozen=True)
class HollandParams:
    rmax_m: float
    b: float
    dp_pa: float
    f: float
    v_mg: float
    b_clipped: bool
    b_source: str  # "solved" | "clipped" | "default"


def fit_holland(
    v_sfc_ms: float, v_trans_ms: float, rmax_km: float, lat_deg: float, pc_hpa: float | None
) -> HollandParams:
    """Fits Holland parameters to a surface intensity (ENGINE §3)."""
    f = coriolis(lat_deg)
    rmax_m = rmax_km * 1000.0
    v_mg = max((v_sfc_ms - 0.5 * v_trans_ms) / K_SEA, 1.0)
    if pc_hpa is not None and np.isfinite(pc_hpa) and pc_hpa < 1010.0:
        dp = (1010.0 - pc_hpa) * 100.0  # ambient pressure p_n = 1010 hPa (PRIOR)

        def err(b: float) -> float:
            return max_gradient_wind(rmax_m, b, dp, f)[0] - v_mg

        try:
            b = float(brentq(err, 0.3, 4.0, xtol=1e-4))
        except ValueError:
            b = RHO_AIR * np.e * v_mg**2 / dp  # Holland's closed form as a fallback
        b_clip = float(np.clip(b, *B_CLIP))
        return HollandParams(
            rmax_m, b_clip, dp, f, v_mg, b_clip != b, "clipped" if b_clip != b else "solved"
        )

    def err_dp(dp: float) -> float:
        return max_gradient_wind(rmax_m, B_DEFAULT, dp, f)[0] - v_mg

    dp = float(brentq(err_dp, 1.0, 30_000.0, xtol=0.1))
    return HollandParams(rmax_m, B_DEFAULT, dp, f, v_mg, False, "default")


def local_offsets_m(
    lon0: float, lat0: float, lon: NDArray[np.float64], lat: NDArray[np.float64]
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """East and north offsets (m) of points from a storm centre (local equirectangular)."""
    dx = np.radians(lon - lon0) * EARTH_RADIUS_M * np.cos(np.radians((lat + lat0) / 2))
    dy = np.radians(lat - lat0) * EARTH_RADIUS_M
    return dx, dy


def surface_wind(  # noqa: PLR0917 - numeric kernel, called per member and hour
    p: HollandParams,
    lon0: float,
    lat0: float,
    trans_u: float,
    trans_v: float,
    lon: ArrayLike,
    lat: ArrayLike,
    over_land: ArrayLike | bool = True,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Sustained surface wind and gust (m/s) at points, for one member at one time.

    ``trans_u``/``trans_v`` are the storm's translation velocity (m/s, east/north). Northern
    Hemisphere rotation (counter-clockwise) with inflow toward the centre.
    """
    lon_a = np.asarray(lon, dtype=np.float64)
    lat_a = np.asarray(lat, dtype=np.float64)
    dx, dy = local_offsets_m(lon0, lat0, lon_a, lat_a)
    r = np.hypot(dx, dy)
    vg = gradient_wind(r, p.rmax_m, p.b, p.dp_pa, p.f)
    k = np.where(np.asarray(over_land, dtype=bool), K_SEA * LAND_FACTOR, K_SEA)
    rr = np.maximum(r, 1.0)
    # Unit vectors: tangential (counter-clockwise) rotated inward by the inflow angle.
    tx, ty = -dy / rr, dx / rr
    ex, ey = dx / rr, dy / rr
    a = np.radians(INFLOW_DEG)
    wx, wy = np.cos(a) * tx - np.sin(a) * ex, np.cos(a) * ty - np.sin(a) * ey
    v = k * vg + 0.5 * (trans_u * wx + trans_v * wy)
    v = np.maximum(v, 0.0)
    return v, GUST_FACTOR * v


def translation_velocity(
    lon: NDArray[np.float64], lat: NDArray[np.float64], hours: NDArray[np.float64]
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Storm translation velocity (m/s east, north) along a track, by central differences."""
    if len(lon) < 2:
        return np.zeros(len(lon)), np.zeros(len(lon))
    dx, dy = local_offsets_m(lon[0], lat[0], lon, lat)
    t = hours * 3600.0
    return np.gradient(dx, t), np.gradient(dy, t)
