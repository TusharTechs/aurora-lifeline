"""Settlements as H3 cells with WorldPop population (DATA §2 row 5).

Slice rule: a settlement is an H3 resolution-8 cell (about 0.74 km^2) whose WorldPop 2020 100 m
population, summed over the pixel centres that fall in it, is at least 25 (PRIOR). The cell
centroid is the settlement point; the cell polygon is its hull. DBSCAN clustering is Demo Day work.
"""

from pathlib import Path

import geopandas as gpd
import h3
import numpy as np
import pandas as pd
import rasterio
from rasterio.windows import from_bounds
from shapely.geometry import Point, Polygon
from shapely.geometry.base import BaseGeometry

H3_RES = 8
MIN_POPULATION = 25.0  # PRIOR


def population_by_cell(raster: Path, area: BaseGeometry, res: int = H3_RES) -> pd.Series:
    """Sums raster population over pixel centres inside ``area`` (EPSG:4326), grouped by H3 cell."""
    w, s, e, n = area.bounds
    with rasterio.open(raster) as ds:
        window = from_bounds(w, s, e, n, ds.transform).round_offsets().round_lengths()
        data = ds.read(1, window=window, masked=True)
        transform = ds.window_transform(window)
    values = np.ma.filled(data.astype("float64"), 0.0)
    rows, cols = np.nonzero(values > 0)
    if rows.size == 0:
        return pd.Series(dtype="float64", name="population")
    xs, ys = rasterio.transform.xy(transform, rows, cols, offset="center")
    lon, lat = np.asarray(xs), np.asarray(ys)
    cells = np.fromiter(
        (h3.latlng_to_cell(a, b, res) for a, b in zip(lat, lon, strict=True)), dtype=object
    )
    pop = pd.Series(values[rows, cols], index=cells, name="population")
    return pop.groupby(level=0).sum()


def settlements_from_population(
    pop: pd.Series, area: BaseGeometry, min_population: float = MIN_POPULATION
) -> gpd.GeoDataFrame:
    """Builds the settlements table from per-cell population, keeping cells centred in ``area``."""
    pop = pop[pop >= min_population].sort_index()
    rows = []
    for cell, p in pop.items():
        lat, lon = h3.cell_to_latlng(cell)
        centre = Point(lon, lat)
        if not area.contains(centre):
            continue
        hull = Polygon([(b, a) for a, b in h3.cell_to_boundary(cell)])
        rows.append(
            {"settlement_id": cell, "population": float(p), "geometry": centre, "hull": hull}
        )
    out = gpd.GeoDataFrame(rows, geometry="geometry", crs=4326)
    if not out.empty:
        out["hull"] = gpd.GeoSeries(out["hull"], crs=4326)
    return out
