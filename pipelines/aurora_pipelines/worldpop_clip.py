"""Clips the WorldPop 2020 India raster to the configured states and writes a compact GeoTIFF.

data.worldpop.org ignores HTTP range requests, so the 1.84 GB India file is downloaded once,
clipped here to a bounding box around Andhra Pradesh and Odisha, and can then be deleted.

Usage:
    python -m aurora_pipelines.worldpop_clip --src data/raw/worldpop/2020/ind_ppp_2020.tif \
        --dst data/raw/worldpop/2020/ind_ppp_2020_ap_od.tif --bbox 76.7 12.5 87.6 22.7
"""

import argparse
import hashlib
import sys
from pathlib import Path

import rasterio
from rasterio.windows import from_bounds


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--src", type=Path, required=True)
    ap.add_argument("--dst", type=Path, required=True)
    ap.add_argument("--bbox", type=float, nargs=4, metavar=("W", "S", "E", "N"), required=True)
    args = ap.parse_args()
    with rasterio.open(args.src) as ds:
        window = from_bounds(*args.bbox, ds.transform).round_offsets().round_lengths()
        profile = ds.profile | {
            "height": int(window.height),
            "width": int(window.width),
            "transform": ds.window_transform(window),
            "compress": "deflate",
            "predictor": 3,
            "tiled": True,
            "blockxsize": 512,
            "blockysize": 512,
        }
        data = ds.read(1, window=window)
    with rasterio.open(args.dst, "w", **profile) as out:
        out.write(data, 1)
    digest = hashlib.sha256(args.dst.read_bytes()).hexdigest()
    (args.dst.parent / "sha256sums.txt").write_text(f"{digest}  {args.dst.name}\n")
    print(f"wrote {args.dst} ({args.dst.stat().st_size / 1e6:.0f} MB), window {window}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
