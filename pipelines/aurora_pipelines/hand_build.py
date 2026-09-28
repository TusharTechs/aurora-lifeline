"""Builds a 90 m HAND raster for a region from Copernicus GLO-30 and JRC surface water.

Fallback for MERIT Hydro ``hnd`` (ENGINE §5, DATA §2 row 7) so rain flooding does not wait on
Earth Engine. Writes hand_90m.tif and flowacc_90m.tif next to the region's graph build.

Usage:
    python -m aurora_pipelines.hand_build --state andhra_pradesh --region godavari_krishna
"""

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
import yaml
from rasterio.enums import Resampling
from rasterio.merge import merge
from rasterio.warp import reproject

from aurora_engine.hand import compute_hand

ROOT = Path(__file__).resolve().parents[2]
RES_DEG = 1 / 1200  # 3 arc-seconds, about 90 m (MERIT Hydro's resolution)
STREAM_CELLS = 124  # about 1 km^2 contributing area at 90 m (PRIOR)
PERMANENT_WATER_OCCURRENCE = 80  # JRC occurrence percent (ENGINE §5)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--state", required=True)
    ap.add_argument("--region", required=True)
    ap.add_argument("--build-id", default=datetime.now(UTC).strftime("%Y%m%d"))
    args = ap.parse_args()
    t0 = time.time()
    out = ROOT / "data/ref" / args.state / args.build_id / args.region
    out.mkdir(parents=True, exist_ok=True)
    cfg = yaml.safe_load((ROOT / f"config/states/{args.state}.yaml").read_text())
    osm_dir = sorted(ROOT.glob(f"data/ref/osm/{cfg['osm_extract']}-*"))[-1]
    roads = gpd.read_parquet(osm_dir / args.region / "roads.parquet", columns=["geometry"])
    w, s, e, n = (float(v) for v in roads.total_bounds)
    w, s, e, n = w - 0.05, s - 0.05, e + 0.05, n + 0.05

    tiles = sorted((ROOT / "data/raw/copernicus_dem/glo30").glob("*.tif"))
    srcs = [rasterio.open(p) for p in tiles]
    dem, transform = merge(
        srcs, bounds=(w, s, e, n), res=RES_DEG, resampling=Resampling.average, nodata=np.nan
    )
    for src in srcs:
        src.close()
    elev = dem[0].astype(np.float64)
    # Copernicus GLO-30 sets the sea to 0 m; missing tiles are NaN. Both are outlets.
    outlet = ~np.isfinite(elev) | (elev <= 0.0)

    water = np.zeros(elev.shape, dtype=np.float32)
    jrc = sorted((ROOT / "data/raw/jrc_gsw/v1_4_2021").glob("occurrence_*.tif"))
    if jrc:
        with rasterio.open(jrc[0]) as ds:
            reproject(
                rasterio.band(ds, 1), water, dst_transform=transform, dst_crs="EPSG:4326",
                resampling=Resampling.max,
            )  # fmt: skip
    permanent = (water >= PERMANENT_WATER_OCCURRENCE) & (water <= 100)
    print(f"grid {elev.shape[1]} x {elev.shape[0]} cells; outlets {outlet.mean():.1%}; "
          f"permanent water {permanent.mean():.1%}; {time.time() - t0:.0f} s")  # fmt: skip

    hand, acc = compute_hand(elev, outlet, permanent_water=permanent, stream_cells=STREAM_CELLS)
    profile = {
        "driver": "GTiff", "height": elev.shape[0], "width": elev.shape[1], "count": 1,
        "dtype": "float32", "crs": "EPSG:4326", "transform": transform, "nodata": np.nan,
        "compress": "deflate", "tiled": True, "blockxsize": 512, "blockysize": 512,
    }  # fmt: skip
    with rasterio.open(out / "hand_90m.tif", "w", **profile) as ds:
        ds.write(hand, 1)
    with rasterio.open(out / "flowacc_90m.tif", "w", **profile) as ds:
        ds.write(acc.astype(np.float32), 1)
    land = np.isfinite(hand) & ~outlet
    pct = {str(q): float(np.nanpercentile(hand[land], q)) for q in (10, 50, 90)}
    meta: dict[str, object] = {
        "method": "priority-flood (Barnes et al. 2014), own code; Copernicus GLO-30 at 90 m",
        "stream_cells": STREAM_CELLS, "stream_status": "PRIOR",
        "permanent_water_occurrence": PERMANENT_WATER_OCCURRENCE,
        "hand_percentiles_land_m": pct,
        "created_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
    }  # fmt: skip
    (out / "hand_meta.json").write_text(json.dumps(meta, indent=2))
    print(f"HAND done in {time.time() - t0:.0f} s; land HAND P10/P50/P90 = "
          f"{[round(v, 1) for v in pct.values()]} m")  # fmt: skip
    return 0


if __name__ == "__main__":
    sys.exit(main())
