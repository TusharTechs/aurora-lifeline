"""Scores a storm run against the Sentinel-1 flood mask (ENGINE §10) and writes validation.json.

Inputs: the GeoTIFF tiles and metadata from ``ee_s1_flood.py`` (downloaded into
data/raw/s1/<storm>/), the run's edge closures and member weights, and the graph build.

* Observed edge: its midpoint pixel was observed (not 255). Observed flooded: the midpoint is
  flooded, or at least 2 of 5 points sampled along the edge are (approximates ENGINE §10's
  "at least 30% of a 15 m buffer" at the mask's 30 m resolution).
* Predicted closed: closed by the observation time in at least 50% of weighted members (the
  official IMD member excluded). Also reported for member 0 (the IMD track) alone. Passes after
  the run horizon are compared with the state at the horizon (closures never reopen in the model).
* Metrics per district: POD, FAR and CSI with the contingency table.
* Baselines, each flagging the same number of edges as AURORA in the district: nearest the IMD
  track; lowest height above drainage (IMD's heavy-rain warnings cover every district).

Usage:
    python -m aurora_pipelines.validate_s1 --storm montha_2025 --run montha_2025_b21
"""

import argparse
import json
import sys
from datetime import UTC, datetime
from itertools import pairwise
from pathlib import Path
from typing import Any

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from shapely import line_interpolate_point

from aurora_engine.weights import member_weights

ROOT = Path(__file__).resolve().parents[2]
FRACTIONS = (0.5, 0.1, 0.3, 0.7, 0.9)  # midpoint first
PRED_SHARE = 0.5
NOT_OBSERVED = 255


def sample_tiles(
    tiles: list[Path], lon: np.ndarray, lat: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Flood flag and obs_h at each point (255 where no tile covers it)."""
    flood = np.full(lon.shape, NOT_OBSERVED, dtype=np.uint8)
    obs_h = np.full(lon.shape, NOT_OBSERVED, dtype=np.uint8)
    for t in tiles:
        with rasterio.open(t) as ds:
            b = ds.bounds
            inside = (lon >= b.left) & (lon < b.right) & (lat > b.bottom) & (lat <= b.top)
            if not inside.any():
                continue
            rows, cols = rasterio.transform.rowcol(ds.transform, lon[inside], lat[inside])
            rows = np.clip(np.asarray(rows), 0, ds.height - 1)
            cols = np.clip(np.asarray(cols), 0, ds.width - 1)
            band1, band2 = ds.read(1), ds.read(2)
            flood[inside] = band1[rows, cols]
            obs_h[inside] = band2[rows, cols]
    return flood, obs_h


def _code(v: object) -> str:
    """District id as a plain string ('' when a point falls outside every district)."""
    if v is None or (isinstance(v, float) and np.isnan(v)) or v is pd.NA:
        return ""
    text = str(v)
    return text[:-2] if text.endswith(".0") and text[:-2].isdigit() else text


def scores(pred: np.ndarray, obs: np.ndarray) -> dict[str, Any]:
    hits = int((pred & obs).sum())
    misses = int((~pred & obs).sum())
    fa = int((pred & ~obs).sum())
    cn = int((~pred & ~obs).sum())

    def ratio(a: int, b: int) -> float | None:
        return round(a / b, 3) if b else None

    return {
        "hits": hits, "misses": misses, "false_alarms": fa, "correct_negatives": cn,
        "pod": ratio(hits, hits + misses), "far": ratio(fa, hits + fa), "csi": ratio(hits, hits + misses + fa),
        "flagged": int(pred.sum()),
    }  # fmt: skip


def flag_top(values: np.ndarray, k: int, smallest: bool = True) -> np.ndarray:
    out = np.zeros(len(values), dtype=bool)
    if k <= 0 or len(values) == 0:
        return out
    order = np.argsort(values if smallest else -values, kind="stable")
    out[order[: min(k, len(values))]] = True
    return out


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--storm", required=True)
    ap.add_argument("--run", required=True)
    args = ap.parse_args()
    s1_dir = ROOT / "data/raw/s1" / args.storm
    meta_s1 = json.loads((s1_dir / "s1_meta.json").read_text())
    tiles = sorted(s1_dir.glob("tile_*.tif"))
    run = ROOT / "data/runs" / args.run
    meta = json.loads((run / "run_meta.json").read_text())
    build = ROOT / meta["build_dir"]
    now = pd.Timestamp(meta["now_utc"])
    horizon = float(meta["horizon_h"])
    t_ref_h = (pd.Timestamp(meta_s1["t_utc"]) - now).total_seconds() / 3600

    edges = gpd.read_parquet(
        build / "edges.parquet", columns=["edge_id", "geometry", "mid_lon", "mid_lat", "min_hand_m"]
    )
    if edges.crs is not None and edges.crs.to_epsg() != 4326:
        edges = edges.to_crs(4326)
    n = len(edges)
    geoms = edges.geometry.to_numpy()
    lon = np.empty((len(FRACTIONS), n))
    lat = np.empty((len(FRACTIONS), n))
    for i, f in enumerate(FRACTIONS):
        pts = line_interpolate_point(geoms, f, normalized=True)
        lon[i] = [p.x for p in pts]
        lat[i] = [p.y for p in pts]
    flood, obs_h = sample_tiles(tiles, lon.ravel(), lat.ravel())
    flood = flood.reshape(lon.shape)
    obs_h = obs_h.reshape(lon.shape)
    observed = flood[0] != NOT_OBSERVED
    n_flood_pts = (flood == 1).sum(axis=0)
    obs_flooded = observed & ((flood[0] == 1) | (n_flood_pts >= 2))
    t_obs = np.where(observed, np.minimum(t_ref_h + obs_h[0].astype(float), horizon), np.nan)

    # Weighted share of members closing each edge by its observation time.
    members = pd.read_parquet(run / "members.parquet")
    w = member_weights(members)
    imd_idx = np.nonzero((members["source"] == "IMD").to_numpy())[0]
    ce = np.load(run / "edge_closures.npz")
    me, hr = ce["member_edge"], ce["hour"]
    m_i, e_i = me[:, 0], me[:, 1]
    by_obs = hr <= np.nan_to_num(t_obs, nan=-1.0)[e_i]
    share = np.bincount(e_i[by_obs], weights=w[m_i[by_obs]], minlength=n)
    pred = observed & (share >= PRED_SHARE)
    pred0 = np.zeros(n, dtype=bool)
    if len(imd_idx):
        sel = by_obs & (m_i == imd_idx[0])
        pred0[e_i[sel]] = True
    pred0 &= observed

    # Districts and the IMD track (for the distance baseline).
    districts = gpd.read_parquet(build / "districts.parquet")[
        ["osm_relation_id", "name", "geometry"]
    ].to_crs(4326)
    mids = gpd.GeoDataFrame(
        geometry=gpd.points_from_xy(edges["mid_lon"], edges["mid_lat"]), crs=4326
    )
    joined = gpd.sjoin(mids, districts, how="left", predicate="within")
    joined = joined[~joined.index.duplicated(keep="first")]
    district_of = np.array([_code(v) for v in joined["osm_relation_id"]], dtype=object)
    tracks = pd.read_parquet(run / "tracks.parquet")
    imd_tr = tracks[tracks["source"] == "IMD"].sort_values("valid_utc")
    track_xy = np.c_[imd_tr["lon"].to_numpy(), imd_tr["lat"].to_numpy()]
    kx = np.cos(np.radians(16.5))
    mx, my = edges["mid_lon"].to_numpy() * kx, edges["mid_lat"].to_numpy()
    d_track = np.full(n, np.inf)
    for (x0, y0), (x1, y1) in pairwise(track_xy):
        ax, ay, bx, by = x0 * kx, y0, x1 * kx, y1
        vx, vy = bx - ax, by - ay
        tt = np.clip(((mx - ax) * vx + (my - ay) * vy) / max(vx * vx + vy * vy, 1e-12), 0, 1)
        d_track = np.minimum(d_track, np.hypot(mx - (ax + tt * vx), my - (ay + tt * vy)))
    hand = edges["min_hand_m"].to_numpy(dtype=float)

    rows = []
    codes = [_code(v) for v in districts["osm_relation_id"]]
    for code, name in zip(codes, districts["name"], strict=True):
        sel = (district_of == code) & observed
        if not sel.any():
            rows.append({"district_lgd": code, "district_name": name, "status": "not observed"})
            continue
        o = obs_flooded[sel]
        k = int(pred[sel].sum())
        rows.append({
            "district_lgd": code,
            "district_name": name,
            "status": "observed",
            "edges_observed": int(sel.sum()),
            "edges_observed_flooded": int(o.sum()),
            "obs_hours_after_landfall": sorted({int(x) for x in obs_h[0][sel] if x != NOT_OBSERVED}),
            "aurora": scores(pred[sel], o),
            "member0_imd_track": scores(pred0[sel], o),
            "baseline_distance_to_track": scores(flag_top(d_track[sel], k), o),
            "baseline_low_hand": scores(flag_top(np.nan_to_num(hand[sel], nan=np.inf), k), o),
        })  # fmt: skip
    obs_all = observed & np.isin(district_of, np.array(codes, dtype=object))
    k_all = int(pred[obs_all].sum())
    total: dict[str, Any] = {
        "edges_observed": int(obs_all.sum()),
        "edges_observed_flooded": int(obs_flooded[obs_all].sum()),
        "aurora": scores(pred[obs_all], obs_flooded[obs_all]),
        "member0_imd_track": scores(pred0[obs_all], obs_flooded[obs_all]),
        "baseline_distance_to_track": scores(
            flag_top(d_track[obs_all], k_all), obs_flooded[obs_all]
        ),
        "baseline_low_hand": scores(
            flag_top(np.nan_to_num(hand[obs_all], nan=np.inf), k_all), obs_flooded[obs_all]
        ),
    }
    out = {
        "run_id": args.run,
        "storm_id": args.storm,
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "reference_time_utc": meta_s1["t_utc"],
        "sentinel1": {
            k: meta_s1[k]
            for k in ("orbits", "window_days", "parameters", "attribution")
            if k in meta_s1
        },
        "rules": {
            "observed_flooded": "midpoint flooded, or at least 2 of 5 points along the edge",
            "predicted_closed": f"closed by the observation time in at least {int(PRED_SHARE * 100)}% of weighted members",
            "after_horizon": f"passes after the {int(horizon)} h run horizon are compared with the state at the horizon",
        },
        "total": total,
        "districts": rows,
        "caveats": [
            "Sentinel-1 sees standing water at the pass time; it can miss the flood peak between passes.",
            "Radar under-detects flooding in built-up areas and under tree cover, so hits there are undercounted.",
            "A flooded pixel at a road is evidence of water near the road, not proof the road was impassable.",
            "The model closes roads for rain flooding and storm surge only, and never reopens them.",
        ],
    }
    (run / "validation.json").write_text(json.dumps(out, indent=1))
    web = ROOT / "apps/web/public/runs" / args.run
    if web.exists():
        (web / "validation.json").write_text(json.dumps(out, separators=(",", ":")))
    t = total["aurora"]
    print(f"observed {total['edges_observed']:,} edges, flooded {total['edges_observed_flooded']:,}; "
          f"AURORA POD {t['pod']} FAR {t['far']} CSI {t['csi']} (flagged {t['flagged']:,})")  # fmt: skip
    return 0


if __name__ == "__main__":
    sys.exit(main())
