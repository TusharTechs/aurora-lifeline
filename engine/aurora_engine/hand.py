"""Height above nearest drainage (HAND) from a DEM, with our own priority-flood (ENGINE §5).

Used when MERIT Hydro's ``hnd`` band is not yet available (it needs Earth Engine or a registered
download). Steps, all O(N log N) or better and compiled with numba:

1. Priority-flood from outlets (grid edges, sea and nodata cells), after Barnes, Lehman & Mulla
   (2014), "Priority-Flood". Every cell is reached from a lower or equal neighbour; the cell that
   reaches it first is where it drains, so flats and pits are routed without a separate fill step.
2. Flow accumulation in reverse discovery order.
3. Drainage cells: accumulation at least ``stream_cells`` (about 1 km^2 at 90 m, PRIOR), plus
   permanent water and the sea.
4. HAND = elevation minus the elevation of the drainage cell reached by following the flow path.

The DEM is a surface model (Copernicus GLO-30), so buildings and trees raise HAND locally; the
proof page states this. Outputs are float32 metres, NaN where the DEM has no data.
"""

from pathlib import Path
from typing import TYPE_CHECKING

import numba as nb
import numpy as np
from numpy.typing import NDArray

if TYPE_CHECKING:
    import geopandas as gpd

# 8-neighbour offsets (row, col)
_DR = np.array([-1, -1, -1, 0, 0, 1, 1, 1], dtype=np.int64)
_DC = np.array([-1, 0, 1, -1, 1, -1, 0, 1], dtype=np.int64)


@nb.njit(cache=True)
def _heappush(hv, hi, n, v, i):  # type: ignore[no-untyped-def]
    hv[n] = v
    hi[n] = i
    k = n
    while k > 0:
        p = (k - 1) >> 1
        if hv[k] < hv[p] or (hv[k] == hv[p] and hi[k] < hi[p]):
            hv[k], hv[p] = hv[p], hv[k]
            hi[k], hi[p] = hi[p], hi[k]
            k = p
        else:
            break
    return n + 1


@nb.njit(cache=True)
def _heappop(hv, hi, n):  # type: ignore[no-untyped-def]
    v, i = hv[0], hi[0]
    n -= 1
    hv[0], hi[0] = hv[n], hi[n]
    k = 0
    while True:
        a = 2 * k + 1
        b = a + 1
        m = k
        if a < n and (hv[a] < hv[m] or (hv[a] == hv[m] and hi[a] < hi[m])):
            m = a
        if b < n and (hv[b] < hv[m] or (hv[b] == hv[m] and hi[b] < hi[m])):
            m = b
        if m == k:
            break
        hv[k], hv[m] = hv[m], hv[k]
        hi[k], hi[m] = hi[m], hi[k]
        k = m
    return v, i, n


@nb.njit(cache=True)
def _priority_flood(elev, outlet):  # type: ignore[no-untyped-def]
    """Returns (downstream index, discovery order); downstream = -1 for outlets."""
    nr, nc = elev.shape
    n = nr * nc
    flat = elev.ravel()
    down = np.full(n, -1, dtype=np.int64)
    seen = np.zeros(n, dtype=np.bool_)
    order = np.empty(n, dtype=np.int64)
    hv = np.empty(n, dtype=np.float64)
    hi = np.empty(n, dtype=np.int64)
    size = 0
    count = 0
    oflat = outlet.ravel()
    for i in range(n):
        r, c = i // nc, i % nc
        if oflat[i] or r == 0 or c == 0 or r == nr - 1 or c == nc - 1:
            seen[i] = True
            size = _heappush(hv, hi, size, flat[i] if np.isfinite(flat[i]) else -1e9, i)
    level = np.empty(n, dtype=np.float64)
    while size > 0:
        v, i, size = _heappop(hv, hi, size)
        level[i] = v
        order[count] = i
        count += 1
        r, c = i // nc, i % nc
        for k in range(8):
            rr, cc = r + _DR[k], c + _DC[k]
            if rr < 0 or cc < 0 or rr >= nr or cc >= nc:
                continue
            j = rr * nc + cc
            if seen[j]:
                continue
            seen[j] = True
            down[j] = i
            e = flat[j] if np.isfinite(flat[j]) else v
            size = _heappush(hv, hi, size, max(e, v), j)
    return down, order[:count]


@nb.njit(cache=True)
def _accumulate(down, order):  # type: ignore[no-untyped-def]
    acc = np.ones(down.shape[0], dtype=np.float64)
    for k in range(order.shape[0] - 1, -1, -1):
        i = order[k]
        d = down[i]
        if d >= 0:
            acc[d] += acc[i]
    return acc


@nb.njit(cache=True)
def _hand(elev_flat, down, order, drain):  # type: ignore[no-untyped-def]
    n = elev_flat.shape[0]
    base = np.full(n, np.nan)
    for k in range(order.shape[0]):
        i = order[k]
        if drain[i] or down[i] < 0:
            base[i] = elev_flat[i]
        else:
            base[i] = base[down[i]]
    out = elev_flat - base
    for i in range(n):
        if out[i] < 0:
            out[i] = 0.0
    return out


def compute_hand(
    elev: NDArray[np.floating],
    outlet: NDArray[np.bool_],
    permanent_water: NDArray[np.bool_] | None = None,
    stream_cells: int = 124,
) -> tuple[NDArray[np.float32], NDArray[np.float64]]:
    """Computes HAND (m) and flow accumulation (cells) for a DEM grid.

    ``outlet`` marks sea and nodata cells where water leaves the grid. ``stream_cells`` is the
    contributing area that starts a drainage line (124 cells of 90 m is about 1 km^2; PRIOR).
    """
    e = np.asarray(elev, dtype=np.float64)
    down, order = _priority_flood(e, np.asarray(outlet, dtype=np.bool_))
    acc = _accumulate(down, order)
    drain = acc >= stream_cells
    drain |= np.asarray(outlet, dtype=np.bool_).ravel()
    if permanent_water is not None:
        drain |= np.asarray(permanent_water, dtype=np.bool_).ravel()
    hand = _hand(e.ravel(), down, order, drain).reshape(e.shape)
    hand[~np.isfinite(e)] = np.nan
    return hand.astype(np.float32), acc.reshape(e.shape)


def sample_raster(
    path: "str | object", lon: NDArray[np.float64], lat: NDArray[np.float64]
) -> NDArray[np.float64]:
    """Nearest-cell raster values at lon/lat points (EPSG:4326 raster); NaN outside or nodata."""
    import rasterio  # noqa: PLC0415 - keeps the numba kernels importable without GDAL

    with rasterio.open(path) as ds:
        band = ds.read(1).astype(np.float64)
        if ds.nodata is not None and np.isfinite(ds.nodata):
            band[band == ds.nodata] = np.nan
        rows, cols = rasterio.transform.rowcol(ds.transform, lon, lat)
    rows, cols = np.asarray(rows), np.asarray(cols)
    ok = (rows >= 0) & (cols >= 0) & (rows < band.shape[0]) & (cols < band.shape[1])
    out = np.full(len(lon), np.nan)
    out[ok] = band[rows[ok], cols[ok]]
    return out


def edge_hand(
    edges_metric: "gpd.GeoDataFrame",
    hand_path: str | Path,
    step_m: float = 45.0,
    end_m: float = 200.0,
) -> dict[str, NDArray[np.float64]]:
    """Minimum HAND along each edge and within ``end_m`` of each end (ENGINE §5-6).

    ``edges_metric`` is a GeoDataFrame in a metric CRS. Samples every ``step_m`` metres (about half
    a 90 m cell). Returns arrays ``min_hand_m``, ``hand_u_end_m`` and ``hand_v_end_m``; the end
    values drive closures of bridges, culverts and fords through their approaches.
    """
    import geopandas as gpd  # noqa: PLC0415
    import pandas as pd  # noqa: PLC0415
    import shapely  # noqa: PLC0415

    geoms = np.asarray(edges_metric.geometry.values)
    lengths = shapely.length(geoms)
    n_samples = np.maximum(np.ceil(lengths / step_m).astype(int) + 1, 2)
    idx = np.repeat(np.arange(len(geoms)), n_samples)
    frac = np.concatenate([np.linspace(0.0, 1.0, k) for k in n_samples])
    dist = frac * lengths[idx]
    pts = shapely.line_interpolate_point(geoms[idx], dist)
    ll = gpd.GeoSeries(pts, crs=edges_metric.crs).to_crs(4326)
    vals = sample_raster(hand_path, ll.x.to_numpy(), ll.y.to_numpy())
    df = pd.DataFrame({"e": idx, "d": dist, "v": vals, "L": lengths[idx]})
    whole = df.groupby("e")["v"].min()
    u_end = df[df["d"] <= end_m].groupby("e")["v"].min()
    v_end = df[df["d"] >= df["L"] - end_m].groupby("e")["v"].min()
    n = len(geoms)
    return {
        "min_hand_m": whole.reindex(range(n)).to_numpy(),
        "hand_u_end_m": u_end.reindex(range(n)).to_numpy(),
        "hand_v_end_m": v_end.reindex(range(n)).to_numpy(),
    }
