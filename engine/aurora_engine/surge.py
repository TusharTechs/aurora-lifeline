"""Storm-surge screening model: IMD guidance, alongshore shape and a connected bathtub (ENGINE §4).

UI label: "Screening upper bound, not a hydrodynamic model. IMD surge guidance takes precedence."

Per member:

1. Coastal peak. Member 0 uses the bulletin's surge guidance (upper bound). Other members scale it
   by (V_max,m / V_max,0)^2 at landfall.
2. Alongshore shape. The peak sits one R_m to the right of the track at landfall and decays as a
   Gaussian with sigma = 2 R_m (PRIOR).
3. Inland. Water level eta(x) = h_coast(s(x)) - a d(x), a = 0.083 m/km (PRIOR), where d is the
   distance inland and s the alongshore position of the nearest coast point. A cell floods if its
   elevation is below eta and it is 8-connected to the sea through flooded cells.
4. Timing. A coastal stretch is affected while the storm centre is within R_m + 50 km (PRIOR).

The DEM is a surface model, so flooding in built-up and vegetated areas is understated.
"""

from dataclasses import dataclass

import numba as nb
import numpy as np
from numpy.typing import NDArray

DECAY_M_PER_KM = 0.083  # PRIOR
SIGMA_RM = 2.0  # alongshore Gaussian width in units of R_m (PRIOR)
TIMING_BUFFER_KM = 50.0  # PRIOR
CLOSE_DEPTH_M = 0.3


@dataclass
class CoastIndex:
    """A densified coastline and, for candidate low-lying cells, their inland geometry."""

    coast_xy_km: NDArray[np.float64]  # (P, 2) metric coordinates of coast points, 1 km apart
    coast_s_km: NDArray[np.float64]  # (P,) alongshore position
    cell_rc: NDArray[np.int64]  # (C, 2) row, col of candidate cells in the DEM grid
    cell_elev_m: NDArray[np.float64]  # (C,)
    cell_d_km: NDArray[np.float64]  # (C,) distance to the nearest coast point
    cell_coast: NDArray[np.int64]  # (C,) index of the nearest coast point
    cell_seed: NDArray[np.bool_]  # (C,) touches the sea (flood-fill seed)
    neighbours: NDArray[np.int64]  # (C, 8) candidate indices of 8-neighbours, -1 if none


def build_neighbours(cell_rc: NDArray[np.int64], shape: tuple[int, int]) -> NDArray[np.int64]:
    """8-neighbour candidate indices for a sparse set of grid cells."""
    lookup = np.full(shape[0] * shape[1], -1, dtype=np.int64)
    flat = cell_rc[:, 0] * shape[1] + cell_rc[:, 1]
    lookup[flat] = np.arange(len(flat))
    out = np.full((len(flat), 8), -1, dtype=np.int64)
    k = 0
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            r = cell_rc[:, 0] + dr
            c = cell_rc[:, 1] + dc
            ok = (r >= 0) & (c >= 0) & (r < shape[0]) & (c < shape[1])
            out[ok, k] = lookup[r[ok] * shape[1] + c[ok]]
            k += 1
    return out


@nb.njit(cache=True)
def _flood_fill(wet, seed, neighbours):  # type: ignore[no-untyped-def]
    n = wet.shape[0]
    flooded = np.zeros(n, dtype=np.bool_)
    stack = np.empty(n, dtype=np.int64)
    top = 0
    for i in range(n):
        if seed[i] and wet[i]:
            flooded[i] = True
            stack[top] = i
            top += 1
    while top > 0:
        top -= 1
        i = stack[top]
        for k in range(8):
            j = neighbours[i, k]
            if j >= 0 and wet[j] and not flooded[j]:
                flooded[j] = True
                stack[top] = j
                top += 1
    return flooded


def alongshore_profile(
    s_km: NDArray[np.float64], peak_m: float, s_peak_km: float, rmax_km: float
) -> NDArray[np.float64]:
    sigma = SIGMA_RM * rmax_km
    return np.asarray(peak_m * np.exp(-((s_km - s_peak_km) ** 2) / (2 * sigma**2)))


@dataclass(frozen=True)
class MemberSurge:
    """Surge for one member: depth per candidate cell (0 if dry) and onset hour per coast point."""

    depth_m: NDArray[np.float64]
    onset_h: NDArray[np.float64]  # per coast point; inf if never affected
    peak_m: float
    s_peak_km: float


def member_surge(  # noqa: PLR0917 - numeric kernel called once per member
    idx: CoastIndex,
    peak_m: float,
    s_landfall_km: float,
    right_sign: float,
    rmax_km: float,
    track_xy_km: NDArray[np.float64],
    track_hours: NDArray[np.float64],
) -> MemberSurge:
    """Runs the screening model for one member.

    ``right_sign`` is +1 if the right of the track (looking along the motion) points towards
    increasing alongshore s at landfall, else -1. ``track_xy_km`` are hourly storm centres in the
    same metric frame as the coast, at ``track_hours`` after "now".
    """
    s_peak = s_landfall_km + right_sign * rmax_km
    h_coast = alongshore_profile(idx.coast_s_km, peak_m, s_peak, rmax_km)
    eta = h_coast[idx.cell_coast] - DECAY_M_PER_KM * idx.cell_d_km
    wet = idx.cell_elev_m < eta
    flooded = _flood_fill(wet, idx.cell_seed, idx.neighbours)
    depth = np.where(flooded, eta - idx.cell_elev_m, 0.0)
    # Onset: first hour the centre is within R_m + 50 km of each coast point.
    onset = np.full(len(idx.coast_s_km), np.inf)
    if len(track_hours):
        d = np.hypot(
            idx.coast_xy_km[:, None, 0] - track_xy_km[None, :, 0],
            idx.coast_xy_km[:, None, 1] - track_xy_km[None, :, 1],
        )
        near = d <= rmax_km + TIMING_BUFFER_KM
        first = np.argmax(near, axis=1)
        hit = near.any(axis=1)
        onset[hit] = track_hours[first[hit]]
    return MemberSurge(depth_m=depth, onset_h=onset, peak_m=peak_m, s_peak_km=s_peak)


def landfall_on_coast(
    coast_xy_km: NDArray[np.float64],
    coast_s_km: NDArray[np.float64],
    track_xy_km: NDArray[np.float64],
) -> tuple[int, float, float] | None:
    """First track step whose segment crosses the coast polyline.

    Returns (hour index, alongshore s of the crossing, right_sign), or None if it never crosses.
    """
    from shapely import LineString  # noqa: PLC0415

    coast = LineString(coast_xy_km)
    for i in range(len(track_xy_km) - 1):
        seg = LineString(track_xy_km[i : i + 2])
        if not seg.intersects(coast):
            continue
        p = seg.intersection(coast)
        p = p if p.geom_type == "Point" else p.geoms[0] if hasattr(p, "geoms") else p.centroid
        s = float(coast.project(p))
        # Coast tangent (increasing s) and the right-hand normal of the motion.
        s2 = min(s + 1.0, coast.length)
        s1 = max(s - 1.0, 0.0)
        a, b = coast.interpolate(s1), coast.interpolate(s2)
        tx, ty = b.x - a.x, b.y - a.y
        mx, my = track_xy_km[i + 1] - track_xy_km[i]
        right = np.array([my, -mx])
        sign = 1.0 if right @ np.array([tx, ty]) >= 0 else -1.0
        return i + 1, s + float(coast_s_km[0]), sign
    return None
