from pathlib import Path

import h3
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import box

from aurora_engine.settlements import population_by_cell, settlements_from_population

RES = 1 / 1200  # 3 arc-seconds, like WorldPop 100 m


@pytest.fixture
def raster(tmp_path: Path) -> Path:
    path = tmp_path / "pop.tif"
    data = np.zeros((120, 120), dtype="float32")  # 0.1 x 0.1 degree box at 82.0-82.1 E, 16.9-17.0 N
    data[10:20, 10:20] = 2.0  # 100 pixels x 2 = 200 people in a dense patch
    data[100, 100] = 5.0  # a hamlet below the threshold
    data[60, 60] = -99999.0  # nodata
    with rasterio.open(
        path, "w", driver="GTiff", width=120, height=120, count=1, dtype="float32", crs="EPSG:4326",
        transform=from_origin(82.0, 17.0, RES, RES), nodata=-99999.0,
    ) as ds:  # fmt: skip
        ds.write(data, 1)
    return path


def test_population_is_conserved(raster: Path) -> None:
    pop = population_by_cell(raster, box(82.0, 16.9, 82.1, 17.0))
    assert pop.sum() == pytest.approx(205.0)
    assert all(h3.get_resolution(c) == 8 for c in pop.index)


def test_threshold_and_area_filter(raster: Path) -> None:
    area = box(82.0, 16.9, 82.1, 17.0)
    s = settlements_from_population(population_by_cell(raster, area), area)
    assert s["population"].min() >= 25
    assert s["population"].sum() <= 200.0
    assert s["hull"].iloc[0].geom_type == "Polygon"
    assert s["settlement_id"].is_unique
