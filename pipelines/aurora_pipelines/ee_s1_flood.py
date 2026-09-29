# mypy: disable-error-code="no-any-return"
"""Sentinel-1 flood mask for a storm (ENGINE §10), computed in Earth Engine.

Runs in Cloud Shell with only ``earthengine-api`` installed (no engine dependencies). Writes a
metadata JSON and prints download URLs for a 3 x 3 grid of GeoTIFF tiles, each with two bands:

* ``flood``: 1 flooded, 0 observed and not flooded, 255 not observed;
* ``obs_h``: hours after the reference time of the post-event scene used (255 if none).

Method (ENGINE §10, UN-SPIDER practice), per Sentinel-1 relative orbit:
1. pre-event: median IW VV, same relative orbit, T-30 to T-3 days;
2. post-event: first acquisition from T to T+4 days (T+6 if none), per orbit;
3. 50 m focal median on both;
4. flooded = (post - pre < -3 dB) AND (post < -16 dB) AND NOT permanent water (JRC occurrence
   > 80%) AND slope < 5 degrees (Copernicus GLO-30) AND HAND < 15 m (MERIT Hydro hnd).
Orbits are mosaicked earliest first. Contains modified Copernicus Sentinel data [2025].

Usage (Cloud Shell):
    python ee_s1_flood.py --project aurora-lifeline --t 2025-10-28T18:30:00Z \\
        --bbox 80.371 15.442 82.887 17.923 --out s1_montha.json
"""

import argparse
import json
from datetime import UTC, datetime, timedelta

import ee

DIFF_DB = -3.0
POST_MAX_DB = -16.0
JRC_PERM = 80
SLOPE_MAX = 5.0
HAND_MAX = 15.0
FOCAL_M = 50
SCALE_M = 30


def flood_for_orbit(region: ee.Geometry, orbit: int, post: ee.Image, t: datetime) -> ee.Image:
    pre = (
        ee.ImageCollection("COPERNICUS/S1_GRD")
        .filterBounds(region)
        .filter(ee.Filter.eq("instrumentMode", "IW"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
        .filter(ee.Filter.eq("relativeOrbitNumber_start", orbit))
        .filterDate((t - timedelta(days=30)).isoformat(), (t - timedelta(days=3)).isoformat())
        .select("VV")
        .median()
        .focal_median(FOCAL_M, "circle", "meters")
    )
    post_vv = post.select("VV").focal_median(FOCAL_M, "circle", "meters")
    return post_vv.subtract(pre).lt(DIFF_DB).And(post_vv.lt(POST_MAX_DB))


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--project", required=True)
    ap.add_argument("--t", required=True, help="reference time (observed landfall), ISO UTC")
    ap.add_argument("--bbox", type=float, nargs=4, required=True, metavar=("W", "S", "E", "N"))
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    ee.Initialize(project=args.project)
    t = datetime.fromisoformat(args.t.replace("Z", "+00:00")).astimezone(UTC)
    w, s, e, n = args.bbox
    region = ee.Geometry.Rectangle([w, s, e, n])

    def post_scenes(days: int) -> ee.ImageCollection:
        return (
            ee.ImageCollection("COPERNICUS/S1_GRD")
            .filterBounds(region)
            .filter(ee.Filter.eq("instrumentMode", "IW"))
            .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
            .filterDate(t.isoformat(), (t + timedelta(days=days)).isoformat())
            .sort("system:time_start")
        )

    window_days = 4
    scenes = post_scenes(window_days)
    if scenes.size().getInfo() == 0:
        window_days = 6
        scenes = post_scenes(window_days)
    info: list[int] = scenes.aggregate_array("relativeOrbitNumber_start").getInfo() or []
    times: list[int] = scenes.aggregate_array("system:time_start").getInfo() or []
    ids: list[str] = scenes.aggregate_array("system:index").getInfo() or []
    # First acquisition time per relative orbit (all its frames on that pass are mosaicked).
    first: dict[int, int] = {}
    for orb, ms in zip(info, times, strict=True):
        first.setdefault(int(orb), int(ms))
    perm = ee.Image("JRC/GSW1_4/GlobalSurfaceWater").select("occurrence").gt(JRC_PERM).unmask(0)
    dem = (
        ee.ImageCollection("COPERNICUS/DEM/GLO30_2024_1")
        .select("DEM")
        .mosaic()
        .setDefaultProjection("EPSG:4326", None, 30)
    )
    slope = ee.Terrain.slope(dem)
    hand = ee.Image("MERIT/Hydro/v1_0_1").select("hnd")
    valid = perm.Not().And(slope.lt(SLOPE_MAX)).And(hand.lt(HAND_MAX))

    layers = []
    orbits_meta = []
    for orb, ms in sorted(first.items(), key=lambda kv: kv[1]):
        day0 = datetime.fromtimestamp(ms / 1000, UTC)
        same_pass = scenes.filter(ee.Filter.eq("relativeOrbitNumber_start", orb)).filterDate(
            (day0 - timedelta(hours=1)).isoformat(), (day0 + timedelta(hours=1)).isoformat()
        )
        post = same_pass.mosaic()
        footprint = same_pass.geometry()
        obs_h = max(0, min(254, round((day0 - t).total_seconds() / 3600)))
        fl = flood_for_orbit(region, orb, post, t).And(valid)
        observed = post.select("VV").mask().And(ee.Image.constant(1).clip(footprint).mask())
        layer = ee.Image.cat(
            fl.rename("flood").toUint8(), ee.Image.constant(obs_h).rename("obs_h").toUint8()
        ).updateMask(observed)
        layers.append(layer)
        orbits_meta.append(
            {
                "relative_orbit": orb,
                "acquired_utc": day0.isoformat(),
                "hours_after_t": obs_h,
                "scenes": same_pass.size().getInfo(),
            }
        )
    if not layers:
        with open(args.out, "w") as fh:
            json.dump(
                {"status": "no post-event scenes", "t": t.isoformat(), "window_days": window_days},
                fh,
            )
        print("NO POST-EVENT SENTINEL-1 SCENES")
        return 0
    # Earliest pass wins where passes overlap (ENGINE §10: first acquisition).
    mosaic = ee.ImageCollection(layers[::-1]).mosaic().unmask(255).clip(region)

    tiles = []
    grid = 3  # keeps each download well under Earth Engine's request size limit at 30 m
    for i in range(grid):
        for j in range(grid):
            tw, te = w + (e - w) * i / grid, w + (e - w) * (i + 1) / grid
            ts, tn = s + (n - s) * j / grid, s + (n - s) * (j + 1) / grid
            url = mosaic.getDownloadURL(
                {
                    "region": ee.Geometry.Rectangle([tw, ts, te, tn]),
                    "scale": SCALE_M,
                    "crs": "EPSG:4326",
                    "format": "GEO_TIFF",
                    "bands": ["flood", "obs_h"],
                }
            )
            tiles.append({"bbox": [tw, ts, te, tn], "url": url})
    meta = {
        "status": "ok",
        "t_utc": t.isoformat(),
        "window_days": window_days,
        "orbits": orbits_meta,
        "scene_ids": ids,
        "parameters": {
            "diff_db": DIFF_DB,
            "post_max_db": POST_MAX_DB,
            "jrc_permanent_pct": JRC_PERM,
            "slope_max_deg": SLOPE_MAX,
            "hand_max_m": HAND_MAX,
            "focal_median_m": FOCAL_M,
            "scale_m": SCALE_M,
        },
        "sources": [
            "COPERNICUS/S1_GRD",
            "JRC/GSW1_4/GlobalSurfaceWater",
            "COPERNICUS/DEM/GLO30_2024_1",
            "MERIT/Hydro/v1_0_1",
        ],
        "attribution": "Contains modified Copernicus Sentinel data [2025]",
        "tiles": tiles,
    }
    with open(args.out, "w") as fh:
        json.dump(meta, fh, indent=1)
    print(json.dumps({k: v for k, v in meta.items() if k != "tiles"}, indent=1))
    print("===== DOWNLOAD LINKS (paste this block back) =====")
    for tl in tiles:
        print(tl["url"])
    print("==================================================")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
