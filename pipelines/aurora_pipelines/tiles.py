"""Builds the static web layers for a published run (BUILD_PLAN 2.7; ARCHITECTURE §5).

Writes under apps/web/public/:

* runs/<run_id>/districts/<lgd>.json and manifest.json (copied from the run);
* tiles/<run_id>/edges/{z}/{x}/{y}.pbf and tiles/<run_id>/settlements/... (tippecanoe, one run
  per layer, --no-tile-compression). Properties carry closure or isolation deciles in hours since
  "now" (d1..d9; absent = not reached in that share of members) so the client can shade
  P(closed by t) or P(cut off by t);
* runs/<run_id>/tracks.json (ensemble and IMD tracks);
* runs/<run_id>/flood.png and surge.png with overlays.json (bounds and legend): probability of
  water deeper than 0.3 m over the ground by landfall.

tippecanoe (BSD-2) runs as a separate build-time CLI.

Usage:
    python -m aurora_pipelines.tiles --storm montha_2025 --run montha_2025_b21
"""

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

import geopandas as gpd
import h3
import numpy as np
import pandas as pd
import rasterio
import shapely
from numpy.typing import NDArray
from rasterio.features import rasterize

from aurora_engine.rain import H_MAX_M, K_M_PER_MM, R0_MM
from aurora_engine.weights import member_weights

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "apps/web/public"
DECILES = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9])
MAJOR = {"motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link", "secondary"}


def decile_hours(
    member: NDArray[np.int64],
    key: NDArray[np.int64],
    hour: NDArray[np.float64],
    w: NDArray[np.float64],
    n: int,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Unconditional weighted deciles of event hour per key, plus P(event within horizon).

    Decile q is the first hour by which the weighted share of members with the event reaches q;
    NaN if that share never reaches q.
    """
    dec = np.full((n, 9), np.nan)
    p = np.zeros(n)
    order = np.lexsort((hour, key))
    k_s, h_s, w_s = key[order], hour[order], w[member][order]
    uniq, start = np.unique(k_s, return_index=True)
    ends = np.r_[start[1:], len(k_s)]
    for kk, a, b in zip(uniq.tolist(), start.tolist(), ends.tolist(), strict=True):
        cw = np.cumsum(w_s[a:b])
        p[kk] = cw[-1]
        idx = np.searchsorted(cw, DECILES - 1e-12, side="left")
        ok = idx < len(cw)
        dec[kk, ok] = h_s[a:b][idx[ok]]
    return dec, p


# Hour written for a decile the ensemble never reaches. Every feature carries all nine deciles:
# deck.gl decodes vector tiles in binary mode, where a missing numeric property reads as 0, which
# would show "closed at hour 0" for every decile a feature lacks.
NEVER_H = 999


def props_with_deciles(base: dict[str, object], dec: NDArray[np.float64]) -> dict[str, object]:
    out = dict(base)
    for i, v in enumerate(dec, start=1):
        out[f"d{i}"] = round(float(v)) if np.isfinite(v) else NEVER_H
    return out


def tippecanoe(
    geojsonl: Path, out_dir: Path, layer: str, *, minzoom: int, maxzoom: int, extra: list[str]
) -> None:
    if out_dir.exists():
        shutil.rmtree(out_dir)
    cmd = [
        "tippecanoe",
        "-e",
        str(out_dir),
        "-l",
        layer,
        "--no-tile-compression",
        "-Z",
        str(minzoom),
        "-z",
        str(maxzoom),
        "--force",
        "--quiet",
        "-P",
        *extra,
        str(geojsonl),
    ]
    subprocess.run(cmd, check=True)


def write_png(
    path: Path, rgba: NDArray[np.uint8], bounds: tuple[float, float, float, float]
) -> None:
    h, w = rgba.shape[1:]
    transform = rasterio.transform.from_bounds(*bounds, w, h)
    with rasterio.open(
        path, "w", driver="PNG", width=w, height=h, count=4, dtype="uint8", transform=transform
    ) as ds:
        ds.write(rgba)
    aux = path.with_suffix(path.suffix + ".aux.xml")
    aux.unlink(missing_ok=True)


def ramp(
    p: NDArray[np.float64], rgb: tuple[int, int, int], max_alpha: int = 200
) -> NDArray[np.uint8]:
    """Single-hue overlay: colour fixed, opacity proportional to probability (0 = transparent)."""
    out = np.zeros((4, *p.shape), dtype=np.uint8)
    on = p > 0.01
    for i, c in enumerate(rgb):
        out[i][on] = c
    out[3][on] = np.clip(40 + p[on] * (max_alpha - 40), 0, 255).astype(np.uint8)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--storm", required=True)
    ap.add_argument("--run", required=True)
    args = ap.parse_args()
    t0 = time.time()
    run = ROOT / "data/runs" / args.run
    meta = json.loads((run / "run_meta.json").read_text())
    build = ROOT / meta["build_dir"]
    members = pd.read_parquet(run / "members.parquet")
    w = member_weights(members)
    if w.sum() == 0:  # deterministic mode: IMD alone
        w = np.ones(len(members))
    w = w / w.sum()
    web_run = WEB / "runs" / args.run
    web_tiles = WEB / "tiles" / args.run
    (web_run / "districts").mkdir(parents=True, exist_ok=True)
    web_tiles.mkdir(parents=True, exist_ok=True)
    tmp = run / "web_tmp"
    tmp.mkdir(exist_ok=True)

    # District JSON and manifest.
    for f in sorted((run / "districts").glob("*.json")):
        shutil.copy2(f, web_run / "districts" / f.name)
    shutil.copy2(run / "manifest.json", web_run / "manifest.json")
    if (run / "areas.json").exists():
        shutil.copy2(run / "areas.json", web_run / "areas.json")

    # Edges.
    edges = gpd.read_parquet(
        build / "edges.parquet", columns=["road_class", "crossing_type", "geometry"]
    )
    ce = np.load(run / "edge_closures.npz")
    me = ce["member_edge"]
    dec, p = decile_hours(me[:, 0], me[:, 1], ce["hour"].astype(np.float64), w, len(edges))
    geom_json = [json.loads(g) for g in shapely.to_geojson(edges.geometry.to_numpy())]
    path = tmp / "edges.geojsonl"
    with path.open("w") as fh:
        for i, (rc, ct) in enumerate(zip(edges["road_class"], edges["crossing_type"], strict=True)):
            if p[i] <= 0:
                continue  # never closes in any member: nothing to draw over the basemap
            base: dict[str, object] = {"id": i, "rc": rc, "ct": ct, "p": round(float(p[i]), 3)}
            major = rc in MAJOR or ct != "none" or p[i] > 0.05
            feat = {
                "type": "Feature",
                "properties": props_with_deciles(base, dec[i]),
                "geometry": geom_json[i],
                "tippecanoe": {"minzoom": 6 if major else 11},
            }
            fh.write(json.dumps(feat, separators=(",", ":")) + "\n")
    tippecanoe(
        path,
        web_tiles / "edges",
        "edges",
        minzoom=6,
        maxzoom=13,
        extra=["--drop-densest-as-needed", "--no-feature-limit"],
    )
    print(
        f"edges: {len(edges):,} features, {int((p > 0).sum()):,} with closure risk; "
        f"{time.time() - t0:.0f} s"
    )

    # Settlements.
    st = gpd.read_parquet(run / "settlements.parquet")
    bs = np.load(run / "b_settle.npy").astype(np.float64)  # members x settlements
    mm, ss = np.nonzero(np.isfinite(bs) & ~np.isneginf(bs))
    sdec, sp = decile_hours(mm, ss, bs[mm, ss], w, bs.shape[1])
    no_route = np.isneginf(bs).mean(axis=0) > 0.5
    path = tmp / "settlements.geojsonl"
    with path.open("w") as fh:
        for i, (sid, pop) in enumerate(zip(st["settlement_id"], st["population"], strict=True)):
            if sp[i] <= 0 and not no_route[i]:
                continue  # never cut off in any member
            ring = [[lng, lat] for lat, lng in h3.cell_to_boundary(sid)]
            ring.append(ring[0])
            base = {
                "id": sid,
                "pop": round(float(pop)),
                "p": round(float(sp[i]), 3),
                "nr": bool(no_route[i]),
                "dl": str(dl) if pd.notna(dl := st["district_lgd"].iloc[i]) else "",
            }
            feat = {
                "type": "Feature",
                "properties": props_with_deciles(base, sdec[i]),
                "geometry": {"type": "Polygon", "coordinates": [ring]},
            }
            fh.write(json.dumps(feat, separators=(",", ":")) + "\n")
    tippecanoe(
        path,
        web_tiles / "settlements",
        "settlements",
        minzoom=6,
        maxzoom=12,
        extra=["--no-feature-limit", "--no-tile-size-limit"],
    )
    print(f"settlements: {len(st):,} features; {time.time() - t0:.0f} s")

    # Tracks (ensemble thinned to 3-hourly; IMD hourly).
    tr = pd.read_parquet(run / "tracks.parquet")
    now = pd.Timestamp(meta["now_utc"])
    feats = []
    for (src, _), grp in tr.groupby(["source", "member_no"], sort=True):
        g = grp.sort_values("valid_utc")
        mem = int(g["member_no"].iloc[0])
        h = ((g["valid_utc"] - now).dt.total_seconds() / 3600).to_numpy()
        keep = (h % 3 == 0) | (src == "IMD")
        coords = [
            [round(float(x), 3), round(float(y), 3)]
            for x, y in zip(g["lon"][keep], g["lat"][keep], strict=True)
        ]
        if len(coords) >= 2:
            feats.append(
                {
                    "type": "Feature",
                    "properties": {
                        "s": src,
                        "m": mem,
                        "o": src == "IMD",
                        "h0": float(h[keep][0]),
                    },
                    "geometry": {"type": "LineString", "coordinates": coords},
                }
            )
    (web_run / "tracks.json").write_text(
        json.dumps({"type": "FeatureCollection", "features": feats}, separators=(",", ":"))
    )
    print(f"tracks: {len(feats)}; {time.time() - t0:.0f} s")

    # Rain-flood probability overlay by landfall (HAND grid of the region build).
    with rasterio.open(build / "hand_90m.tif") as ds:
        hand = ds.read(1).astype(np.float64)
        transform, crs, (h_px, w_px) = ds.transform, ds.crs, ds.shape
        bounds = tuple(ds.bounds)
    districts = gpd.read_parquet(build / "districts.parquet")
    codes = districts["osm_relation_id"].tolist()
    dgrid = rasterize(
        ((g, i + 1) for i, g in enumerate(districts.geometry)),
        out_shape=(h_px, w_px),
        transform=transform,
        fill=0,
        dtype="int32",
    )
    patches = pd.read_parquet(run / "patches.parquet")
    patch_pos = {
        (d, c): i
        for i, (d, c) in enumerate(zip(patches["district_lgd"], patches["h3"], strict=True))
    }
    rain_lf = np.load(run / "rain_at_landfall.npy").astype(np.float64)  # members x patches
    hstar = np.clip(K_M_PER_MM * (rain_lf - R0_MM), 0.0, H_MAX_M)
    rows, cols = np.nonzero((dgrid > 0) & np.isfinite(hand) & (hand < H_MAX_M))
    xs, ys = rasterio.transform.xy(transform, rows, cols, offset="center")
    cell_patch = np.array(
        [
            patch_pos.get((codes[dgrid[r, c] - 1], h3.latlng_to_cell(y, x, 6)), -1)
            for r, c, x, y in zip(rows, cols, xs, ys, strict=True)
        ],
        dtype=np.int64,
    )
    pflood = np.zeros((h_px, w_px))
    need = hand[rows, cols] + 0.3
    for pidx in np.unique(cell_patch[cell_patch >= 0]):
        sel = cell_patch == pidx
        hs = hstar[:, pidx]
        order = np.argsort(hs)
        hs_sorted, cw = hs[order], np.cumsum(w[order])
        k = np.searchsorted(hs_sorted, need[sel], side="right")
        above = cw[-1] - np.where(k > 0, cw[np.maximum(k - 1, 0)], 0.0)
        pflood[rows[sel], cols[sel]] = above
    write_png(web_run / "flood.png", ramp(pflood, (37, 99, 235)), bounds)

    # Surge probability overlay by landfall.
    sc = pd.read_parquet(run / "surge_cells.parquet")
    gshape = tuple(meta["grid_shape"])
    psurge = np.zeros(gshape)
    psurge[sc["row"].to_numpy(), sc["col"].to_numpy()] = sc["p"].to_numpy()
    gt = meta["grid_transform"]
    g_aff = rasterio.Affine(*gt)
    g_bounds = rasterio.transform.array_bounds(gshape[0], gshape[1], g_aff)
    write_png(
        web_run / "surge.png",
        ramp(psurge, (8, 145, 178)),
        (g_bounds[1], g_bounds[0], g_bounds[3], g_bounds[2]),
    )
    overlays = {
        "flood": {
            "url": f"/runs/{args.run}/flood.png",
            "bounds": [bounds[0], bounds[1], bounds[2], bounds[3]],
            "label": "Rain flooding over 0.3 m by landfall (probability)",
            "crs": str(crs),
        },
        "surge": {
            "url": f"/runs/{args.run}/surge.png",
            "bounds": [g_bounds[1], g_bounds[0], g_bounds[3], g_bounds[2]],
            "label": "Storm surge over 0.3 m by landfall (probability; screening model)",
        },
    }
    (web_run / "overlays.json").write_text(json.dumps(overlays, indent=1))
    shutil.rmtree(tmp)
    total = sum(f.stat().st_size for f in (WEB / "tiles" / args.run).rglob("*") if f.is_file())
    print(f"overlays written; tiles {total / 1e6:.1f} MB; done in {time.time() - t0:.0f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
