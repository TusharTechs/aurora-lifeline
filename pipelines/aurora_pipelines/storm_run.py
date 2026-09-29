"""Runs one storm run end to end on a built region (BUILD_PLAN 2.1-2.5; ARCHITECTURE §4).

Tracks (IMD member 0 + ensembles available at the bulletin's issue time) -> hourly alignment to
IMD -> per member: rain and surge hazards -> edge closure hours -> bottleneck isolation for
settlements (to any public hospital) and facilities (to their referral tier) -> raw member
results under data/runs/<run_id>/. Aggregation and district JSON: aurora_pipelines.publish.

Usage:
    python -m aurora_pipelines.storm_run --storm montha_2025 --run montha_2025_b21 \
        --state andhra_pradesh --region godavari_krishna [--max-members 60]
"""

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from multiprocessing import get_context
from pathlib import Path
from typing import Any

import geopandas as gpd
import h3
import numpy as np
import pandas as pd
import rasterio
import yaml
from rasterio.enums import Resampling
from rasterio.merge import merge
from scipy.spatial import cKDTree
from shapely import length, line_interpolate_point
from shapely.ops import linemerge, unary_union

from aurora_engine.closures import build_edge_index, rain_closure_hours, surge_closure_hours
from aurora_engine.facilities import HOSPITAL_TYPES, REFERRAL_TIERS
from aurora_engine.geo import haversine_km
from aurora_engine.graph import METRIC_CRS
from aurora_engine.rain import (
    PATCH_H3_RES,
    closest_approach_rank,
    cumulative_from_daily,
    daily_rain,
    first_hour_reaching,
    patch_daily_totals,
)
from aurora_engine.reach import build_csr, isolation_times
from aurora_engine.surge import CoastIndex, build_neighbours, landfall_on_coast, member_surge
from aurora_engine.tracks import (
    TRACK_COLUMNS,
    align_to_imd,
    interpolate_hourly,
    match_members,
    read_ecmwf_tc_bufr,
    read_weatherlab_csv,
)
from aurora_engine.units import wind_to_ms
from aurora_engine.weights import member_weights
from aurora_engine.wind import willoughby_rmax_km

ROOT = Path(__file__).resolve().parents[2]
SURGE_MAX_ELEV_M = 4.0  # candidate cells for the surge screen (PRIOR; above any plausible level)
SURGE_MAX_DIST_KM = 40.0
COAST_STEP_KM = 0.25
SITE_FLOOD_DEPTH_M = 0.3  # a facility is unavailable once its site floods this deep (PRIOR)


# ---------------------------------------------------------------- tracks


def imd_track(reading: dict[str, Any]) -> pd.DataFrame:
    t0 = pd.Timestamp(reading["forecast"][0]["valid_at_utc"])
    rows = [
        {
            "source": "IMD",
            "member_no": 0,
            "init_utc": t0,
            "valid_utc": pd.Timestamp(f["valid_at_utc"]),
            "lead_h": f["lead_h"],
            "lat": f["lat"],
            "lon": f["lon"],
            "vmax_ms": wind_to_ms((f["msw_min"] + f["msw_max"]) / 2, f["wind_unit"]),
            "pmin_hpa": np.nan,
            "rmw_km": np.nan,
        }
        for f in reading["forecast"]
    ]
    return pd.DataFrame(rows)[TRACK_COLUMNS]


def ensemble_tracks(
    storm: dict[str, Any], issued: pd.Timestamp
) -> tuple[pd.DataFrame, dict[str, str]]:
    """Latest run of each source available at the bulletin's issue time (SPEC §3)."""
    frames, used = [], {}
    for src, cfg in storm["sources"].items():
        delay = pd.Timedelta(hours=float(cfg["publication_delay_h"]))
        path = ROOT / cfg["path"]
        if cfg["kind"] == "ecmwf_tc_bufr":
            cands = [
                (pd.to_datetime(p.name[:10], format="%Y%m%d%H", utc=True), p)
                for p in path.glob("*.bufr")
            ]
        else:
            cands = [
                (
                    pd.to_datetime(
                        p.name.split("_paired")[0][-16:], format="%Y_%m_%dT%H_%M", utc=True
                    ),
                    p,
                )
                for p in path.glob("*.csv")
            ]
        cands = [c for c in cands if c[0] + delay <= issued]
        if not cands:
            continue
        init, f = max(cands)
        used[src] = f"{init.isoformat()} {f.name}"
        if cfg["kind"] == "ecmwf_tc_bufr":
            frames.append(read_ecmwf_tc_bufr(f, source=src))
        else:
            ids = [
                t
                for t in pd.read_csv(f, comment="#", usecols=["track_id"])["track_id"].unique()
                if str(t).startswith("IO")
            ]
            frames += [read_weatherlab_csv(f, src, tid).assign(storm_id=tid) for tid in ids]
    return (
        pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=TRACK_COLUMNS)
    ), used


# ---------------------------------------------------------------- coast and surge index


def coast_line_km(
    coast_gdf: gpd.GeoDataFrame, bounds: tuple[float, float, float, float]
) -> np.ndarray:
    """The longest merged coastline within bounds, densified every COAST_STEP_KM (metric km)."""
    w, s, e, n = bounds
    sel = coast_gdf.cx[w:e, s:n].to_crs(METRIC_CRS)
    merged = linemerge(unary_union(sel.geometry))
    lines = [merged] if merged.geom_type == "LineString" else list(merged.geoms)
    main = max(lines, key=lambda ln: ln.length)
    d = np.arange(0.0, main.length, COAST_STEP_KM * 1000)
    pts = line_interpolate_point(main, d)
    return np.asarray(np.c_[[p.x for p in pts], [p.y for p in pts]] / 1000.0, dtype=np.float64)


@dataclass
class SurgeGrid:
    index: CoastIndex
    grid_lookup: np.ndarray  # flat grid index -> candidate index (-1 if not a candidate)
    transform: Any
    shape: tuple[int, int]


def build_surge_grid(
    bounds: tuple[float, float, float, float], coast_xy_km: np.ndarray
) -> SurgeGrid:
    tiles = sorted((ROOT / "data/raw/copernicus_dem/glo30").glob("*.tif"))
    srcs = [rasterio.open(p) for p in tiles]
    dem, transform = merge(
        srcs, bounds=bounds, res=1 / 1200, resampling=Resampling.average, nodata=np.nan
    )
    for s in srcs:
        s.close()
    elev = dem[0].astype(np.float64)
    sea = ~np.isfinite(elev) | (elev <= 0.0)
    rows, cols = np.nonzero(~sea & (elev <= SURGE_MAX_ELEV_M))
    xs, ys = rasterio.transform.xy(transform, rows, cols, offset="center")
    pts = gpd.GeoSeries(gpd.points_from_xy(xs, ys), crs=4326).to_crs(METRIC_CRS)
    xy_km = np.c_[pts.x.to_numpy(), pts.y.to_numpy()] / 1000.0
    dist, near = cKDTree(coast_xy_km).query(xy_km)
    keep = dist <= SURGE_MAX_DIST_KM
    rows, cols, dist, near = rows[keep], cols[keep], dist[keep], near[keep]
    rc = np.c_[rows, cols].astype(np.int64)
    # Seeds: candidates with a sea neighbour.
    seed = np.zeros(len(rc), dtype=bool)
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            r, c = (
                np.clip(rows + dr, 0, elev.shape[0] - 1),
                np.clip(cols + dc, 0, elev.shape[1] - 1),
            )
            seed |= sea[r, c]
    idx = CoastIndex(
        coast_xy_km=coast_xy_km,
        coast_s_km=np.asarray(np.arange(len(coast_xy_km)) * COAST_STEP_KM, dtype=np.float64),
        cell_rc=rc,
        cell_elev_m=elev[rows, cols],
        cell_d_km=dist,
        cell_coast=near.astype(np.int64),
        cell_seed=seed,
        neighbours=build_neighbours(rc, elev.shape),
    )
    lookup = np.full(elev.size, -1, dtype=np.int64)
    lookup[rows * elev.shape[1] + cols] = np.arange(len(rc))
    return SurgeGrid(idx, lookup, transform, elev.shape)


def cells_for_points(sg: SurgeGrid, lon: np.ndarray, lat: np.ndarray) -> np.ndarray:
    r, c = rasterio.transform.rowcol(sg.transform, lon, lat)
    r, c = np.asarray(r), np.asarray(c)
    ok = (r >= 0) & (c >= 0) & (r < sg.shape[0]) & (c < sg.shape[1])
    out = np.full(len(lon), -1, dtype=np.int64)
    out[ok] = sg.grid_lookup[r[ok] * sg.shape[1] + c[ok]]
    return out


def edge_surge_cells(sg: SurgeGrid, edges: gpd.GeoDataFrame) -> np.ndarray:
    """Per edge, the lowest candidate cell along it (sampled about every 45 m), -1 if none."""
    near = edges["coast_dist_km"].to_numpy() <= SURGE_MAX_DIST_KM
    out = np.full(len(edges), -1, dtype=np.int64)
    sub = edges.loc[near].to_crs(METRIC_CRS)
    geoms = np.asarray(sub.geometry.values)
    lens = length(geoms)
    k = np.maximum(np.ceil(lens / 45.0).astype(int) + 1, 2)
    idx = np.repeat(np.arange(len(geoms)), k)
    frac = np.concatenate([np.linspace(0, 1, n) for n in k])
    pts = gpd.GeoSeries(
        line_interpolate_point(geoms[idx], frac * lens[idx]), crs=METRIC_CRS
    ).to_crs(4326)
    cells = cells_for_points(sg, pts.x.to_numpy(), pts.y.to_numpy())
    elev = np.where(cells >= 0, sg.index.cell_elev_m[np.maximum(cells, 0)], np.inf)
    df = pd.DataFrame({"e": idx, "cell": cells, "elev": elev})
    best = df[df["cell"] >= 0].sort_values(["e", "elev"]).groupby("e")["cell"].first()
    sub_out = np.full(len(geoms), -1, dtype=np.int64)
    sub_out[best.index.to_numpy()] = best.to_numpy()
    out[np.nonzero(near)[0]] = sub_out
    return out


# ---------------------------------------------------------------- per-member worker


G: dict[str, Any] = {}  # read-only state shared with forked workers


def _member(k: int) -> dict[str, Any]:
    m = G["members"][k]
    hours = G["hours"]
    # Rain: per-patch cumulative curves; patches drawn per district and day (ENGINE §5, D22).
    n_h = int(hours[-1])
    cum = np.zeros((G["n_patches"], n_h + 1))
    for i, d in enumerate(G["district_names"]):
        pidx = G["district_patches"][i]
        if len(pidx) == 0:
            continue
        rows = G["daily"][G["daily"]["district"] == d]
        totals = patch_daily_totals(
            rows,
            G["days"],
            len(pidx),
            float(m["q"][i]),
            f"{G['run_id']}|{m['source']}|{m['member_no']}|{d}",
        )
        cum[pidx] = cumulative_from_daily(totals, G["days"], G["now"], n_h)
    close = rain_closure_hours(G["eidx"], cum)
    site_rain = np.full(len(G["fac_node_pos"]), np.inf)
    for j, (pp, thr) in enumerate(zip(G["fac_patch"], G["fac_rain_thr"], strict=True)):
        if pp >= 0 and np.isfinite(thr):
            site_rain[j] = first_hour_reaching(cum[pp], np.array([thr]))[0]
    # Surge.
    surge_peak, s_peak = 0.0, np.nan
    empty_i, empty_f = np.zeros(0, dtype=np.int32), np.zeros(0, dtype=np.float32)
    surge_out = (empty_i, empty_f, empty_f)
    site_surge = np.full(len(G["fac_node_pos"]), np.inf)
    if m["landfall"] is not None:
        _, s_lf, sign = m["landfall"]
        ms = member_surge(
            G["sg"].index,
            m["surge_peak_m"],
            s_lf,
            sign,
            m["rmax_km"],
            m["track_xy_km"],
            m["track_h"],
        )
        onset_cell = ms.onset_h[G["sg"].index.cell_coast]
        close = np.minimum(close, surge_closure_hours(G["eidx"], ms.depth_m, onset_cell))
        fc = G["fac_cells"]
        ok = fc >= 0
        site_surge[ok] = np.where(
            ms.depth_m[fc[ok]] > SITE_FLOOD_DEPTH_M, onset_cell[fc[ok]], np.inf
        )
        surge_peak, s_peak = ms.peak_m, ms.s_peak_km
        wet_cells = np.nonzero(ms.depth_m > SITE_FLOOD_DEPTH_M)[0]
        surge_out = (
            wet_cells.astype(np.int32),
            ms.depth_m[wet_cells].astype(np.float32),
            onset_cell[wet_cells].astype(np.float32),
        )
    avail = np.minimum(site_rain, site_surge)
    csr = G["csr"]
    # Settlements and facilities -> any public hospital.
    hosp = G["hosp_fac"]
    b_any, _ = isolation_times(csr, close, G["fac_node_pos"][hosp], avail[hosp])
    out = {
        "k": k,
        "b_settle": b_any[G["set_node_pos"]].astype(np.float32),
        "b_fac_any": b_any[G["fac_node_pos"]].astype(np.float32),
        "b_fac_ref": np.full(len(G["fac_node_pos"]), np.nan, dtype=np.float32),
        "closed_edges": np.nonzero(np.isfinite(close))[0].astype(np.int32),
        "closed_hours": close[np.isfinite(close)].astype(np.float32),
        "surge_peak_m": surge_peak,
        "s_peak_km": s_peak,
        "surge": surge_out,
        "rain_lf": cum[:, G["landfall_idx"]].astype(np.float32),
    }
    # Referral tiers.
    for tier, targets in REFERRAL_TIERS.items():
        tgt = np.nonzero(np.isin(G["fac_type"], targets))[0]
        who = np.nonzero(G["fac_type"] == tier)[0]
        if len(tgt) == 0 or len(who) == 0:
            continue
        b_ref, _ = isolation_times(csr, close, G["fac_node_pos"][tgt], avail[tgt])
        out["b_fac_ref"][who] = b_ref[G["fac_node_pos"][who]]
    return out


# ---------------------------------------------------------------- main


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--storm", required=True)
    ap.add_argument("--run", required=True)
    ap.add_argument("--state", required=True)
    ap.add_argument("--region", required=True)
    ap.add_argument("--build-id", default=None)
    ap.add_argument("--max-members", type=int, default=0, help="dev only: subsample each source")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    args = ap.parse_args()
    t0 = time.time()
    storm = yaml.safe_load((ROOT / f"config/storms/{args.storm}.yaml").read_text())
    run_cfg = next(r for r in storm["runs"] if r["run_id"] == args.run)
    reading = json.loads((ROOT / run_cfg["bulletin"]["reading"]).read_text())
    issued = pd.Timestamp(run_cfg["bulletin"]["issued_at_utc"])
    now = issued.floor("h")
    build_dir = sorted(
        (ROOT / "data/ref" / args.state).glob(f"{args.build_id or '*'}/{args.region}")
    )[-1]
    out = ROOT / "data/runs" / args.run
    out.mkdir(parents=True, exist_ok=True)

    # Tracks.
    imd = imd_track(reading)
    ens, used = ensemble_tracks(storm, issued)
    matched = match_members(ens, imd)
    if args.max_members:
        keep = (
            matched.groupby("source")["member_no"]
            .unique()
            .map(lambda a: set(sorted(a)[: args.max_members]))
        )
        matched = matched[
            [mn in keep[s] for s, mn in zip(matched["source"], matched["member_no"], strict=True)]
        ]
    imd_h = interpolate_hourly(imd)
    aligned, align_report = (
        align_to_imd(interpolate_hourly(matched), imd_h) if len(matched) else (matched, None)
    )
    tracks = pd.concat([imd_h, aligned], ignore_index=True)
    tracks = tracks[tracks["valid_utc"] >= now]
    tracks.to_parquet(out / "tracks.parquet", index=False)
    counts = tracks.groupby("source")["member_no"].nunique().to_dict()
    # Record only runs that contributed members (a run can exist yet hold no track of this storm).
    used = {k: v for k, v in used.items() if counts.get(k, 0) > 0}
    print(f"members: {counts}; runs used: {used}; {time.time() - t0:.0f} s")

    # Reference data.
    nodes = pd.read_parquet(
        build_dir / "nodes.parquet", columns=["node_id", "district_lgd", "hand_m"]
    )
    edges = gpd.read_parquet(build_dir / "edges.parquet")
    fac = gpd.read_parquet(build_dir / "facilities.parquet")
    fac = fac[fac["type"].isin([*HOSPITAL_TYPES, "shelter"]) & ~fac["unsnapped"]].reset_index(
        drop=True
    )
    settle = gpd.read_parquet(build_dir / "settlements.parquet")
    districts = gpd.read_parquet(build_dir / "districts.parquet")
    state_cfg = yaml.safe_load((ROOT / f"config/states/{args.state}.yaml").read_text())
    dcsv = pd.read_csv(ROOT / state_cfg["districts_csv"], dtype=str).fillna("")
    district_codes = districts["osm_relation_id"].tolist()
    district_names = districts["name"].tolist()

    # Edges outside the region districts take the nearest region district's rain.
    mid = gpd.GeoDataFrame(
        geometry=gpd.points_from_xy(edges["mid_lon"], edges["mid_lat"]), crs=4326
    ).to_crs(METRIC_CRS)
    near = gpd.sjoin_nearest(
        mid, districts[["osm_relation_id", "geometry"]].to_crs(METRIC_CRS), how="left"
    )
    edges["district_lgd"] = near.groupby(level=0)["osm_relation_id"].first().to_numpy()

    node_pos = pd.Index(nodes["node_id"])
    csr = build_csr(
        node_pos.get_indexer(edges["u"]).astype(np.int64),
        node_pos.get_indexer(edges["v"]).astype(np.int64),
        len(nodes),
    )

    # Coast and surge.
    osm_dir = sorted((ROOT / "data/ref/osm").glob(f"{state_cfg['osm_extract']}-*"))[-1]
    coast = gpd.read_parquet(osm_dir / "coastline.parquet")
    w, s, e, n = (float(v) for v in edges.total_bounds)
    bounds = (w - 0.05, s - 0.05, e + 0.05, n + 0.05)
    coast_xy = coast_line_km(coast, bounds)
    sg = build_surge_grid(bounds, coast_xy)
    coast_s = np.asarray(np.arange(len(coast_xy)) * COAST_STEP_KM, dtype=np.float64)
    # Rain patches: (district, H3 res-6 cell of the edge midpoint).
    edge_cell = [
        h3.latlng_to_cell(la, lo, PATCH_H3_RES)
        for la, lo in zip(edges["mid_lat"], edges["mid_lon"], strict=True)
    ]
    patch_keys = pd.Series(list(zip(edges["district_lgd"], edge_cell, strict=True)))
    uniq = sorted(set(patch_keys))
    patch_pos = {k: i for i, k in enumerate(uniq)}
    edge_patch = patch_keys.map(patch_pos).to_numpy(dtype=np.int64)
    eidx = build_edge_index(edges, edge_patch, len(uniq), edge_surge_cells(sg, edges))
    district_patches = [
        np.array([patch_pos[k] for k in uniq if k[0] == c], dtype=np.int64) for c in district_codes
    ]
    print(
        f"surge grid: {len(sg.index.cell_rc):,} low-lying cells; "
        f"coast {len(coast_xy) * COAST_STEP_KM:.0f} km; "
        f"edges with a surge cell {(eidx.surge_cell >= 0).mean():.1%}; {time.time() - t0:.0f} s"
    )

    # Rain categories from the bulletin (ENGINE §5).
    issued = pd.Timestamp(reading["issued_at_utc"])
    dr = daily_rain(
        reading["rainfall_warnings"], dcsv, state_cfg["name"], issued.year, issued.month,
        region_phrases=state_cfg.get("imd_region_phrases"),
    )  # fmt: skip
    daily = dr.table[dr.table["district"].isin(district_names)]
    days = sorted(set(daily["day"]))

    # Landfall of member 0 and the horizon.
    track_xy = {}
    for (src, mem), g in tracks.groupby(["source", "member_no"], sort=True):
        p = gpd.GeoSeries(gpd.points_from_xy(g["lon"], g["lat"]), crs=4326).to_crs(METRIC_CRS)
        track_xy[(src, mem)] = (
            np.c_[p.x, p.y] / 1000.0,
            ((g["valid_utc"] - now).dt.total_seconds() / 3600).to_numpy(),
            g,
        )
    xy0, h0, g0 = track_xy[("IMD", 0)]
    lf0 = landfall_on_coast(coast_xy, coast_s, xy0)
    landfall_h = float(h0[lf0[0]]) if lf0 else float(h0[-1])
    horizon_h = math.ceil(landfall_h + 24)
    hours = np.arange(0, horizon_h + 1, dtype=float)
    v0 = float(np.interp(landfall_h, h0, g0["vmax_ms"].to_numpy()))
    surge_m0 = max((x["height_m_max"] or 0) for x in reading["surge"]) if reading["surge"] else 0.0
    print(
        f"member 0 landfall at +{landfall_h:.0f} h ({now + pd.Timedelta(hours=landfall_h)}); "
        f"horizon {horizon_h} h; "
        f"IMD surge guidance {surge_m0} m"
    )

    # Member table: quantiles per district, landfall, surge peak.
    cent = districts.to_crs(METRIC_CRS).geometry.centroid
    cent_ll = gpd.GeoSeries(cent, crs=METRIC_CRS).to_crs(4326)
    members = []
    for xy, hh, g in track_xy.values():
        sel = hh <= horizon_h
        dmin = np.array(
            [
                float(
                    np.min(
                        haversine_km(g["lat"].to_numpy()[sel], g["lon"].to_numpy()[sel], c.y, c.x)
                    )
                )
                for c in cent_ll
            ]
        )
        lf = landfall_on_coast(coast_xy, coast_s, xy[sel])
        vm = float(g["vmax_ms"].to_numpy()[lf[0]]) if lf else np.nan
        rm = g["rmw_km"].to_numpy()[lf[0]] if lf else np.nan
        lat_lf = float(g["lat"].to_numpy()[lf[0]]) if lf else 16.5
        rmax = (
            float(rm)
            if np.isfinite(rm) and rm > 5
            else willoughby_rmax_km(vm if np.isfinite(vm) else 25.0, lat_lf)
        )
        members.append(
            {
                "source": str(g["source"].iloc[0]),
                "member_no": int(g["member_no"].iloc[0]),
                "dmin": dmin,
                "landfall": lf,
                "surge_peak_m": surge_m0 * (vm / v0) ** 2 if lf else 0.0,
                "rmax_km": rmax,
                "track_xy_km": xy[sel],
                "track_h": hh[sel],
            }
        )
    dm = np.array([m["dmin"] for m in members])  # members x districts
    for j in range(dm.shape[1]):
        q = closest_approach_rank(dm[:, j])
        for i, m in enumerate(members):
            m.setdefault("q", np.zeros(dm.shape[1]))[j] = 0.5 if m["source"] == "IMD" else q[i]

    # Facility inputs.
    fac_node_pos = node_pos.get_indexer(fac["node_id"]).astype(np.int64)
    fac_ll = fac.to_crs(4326)
    fac_d = gpd.sjoin_nearest(
        fac_ll[["geometry"]].to_crs(METRIC_CRS),
        districts[["osm_relation_id", "geometry"]].to_crs(METRIC_CRS),
        how="left",
    )
    fac_dist = fac_d.groupby(level=0)["osm_relation_id"].first().to_numpy()
    fac_cell = [h3.latlng_to_cell(p.y, p.x, PATCH_H3_RES) for p in fac_ll.geometry]
    fac_patch = np.array(
        [patch_pos.get((dcode, c), -1) for dcode, c in zip(fac_dist, fac_cell, strict=True)],
        dtype=np.int64,
    )
    G.update(
        members=members,
        hours=hours,
        now=now.to_pydatetime(),
        daily=daily,
        district_names=district_names,
        eidx=eidx,
        sg=sg,
        csr=csr,
        fac_node_pos=fac_node_pos,
        fac_type=fac["type"].to_numpy(),
        hosp_fac=np.nonzero(fac["type"].isin(HOSPITAL_TYPES).to_numpy())[0],
        fac_cells=cells_for_points(sg, fac_ll.geometry.x.to_numpy(), fac_ll.geometry.y.to_numpy()),
        fac_patch=fac_patch,
        n_patches=len(uniq),
        district_patches=district_patches,
        days=days,
        run_id=args.run,
        fac_rain_thr=np.where(
            np.isfinite(fac["hand_m"]),
            50 + (fac["hand_m"].to_numpy() + SITE_FLOOD_DEPTH_M) / 0.02,
            np.inf,
        ),
        set_node_pos=node_pos.get_indexer(settle["node_id"]).astype(np.int64),
        landfall_idx=int(np.clip(round(landfall_h), 0, horizon_h)),
    )

    # Run members in parallel (fork shares G read-only).
    t1 = time.time()
    with get_context("fork").Pool(args.workers) as pool:
        results = pool.map(_member, range(len(members)), chunksize=4)
    results.sort(key=lambda r: r["k"])
    print(f"ran {len(results)} members on {args.workers} workers in {time.time() - t1:.0f} s")

    # Save raw member results.
    meta = pd.DataFrame(
        [
            {
                "source": m["source"],
                "member_no": m["member_no"],
                "landfall": m["landfall"] is not None,
                "surge_peak_m": r["surge_peak_m"],
                "rmax_km": m["rmax_km"],
            }
            for m, r in zip(members, results, strict=True)
        ]
    )
    meta.to_parquet(out / "members.parquet", index=False)
    np.save(out / "b_settle.npy", np.stack([r["b_settle"] for r in results]))
    np.save(out / "b_fac_any.npy", np.stack([r["b_fac_any"] for r in results]))
    np.save(out / "b_fac_ref.npy", np.stack([r["b_fac_ref"] for r in results]))
    ce = np.concatenate(
        [np.c_[np.full(len(r["closed_edges"]), r["k"]), r["closed_edges"]] for r in results]
    )
    ch = np.concatenate([r["closed_hours"] for r in results])
    np.savez_compressed(out / "edge_closures.npz", member_edge=ce.astype(np.int32), hour=ch)
    # Rain at landfall per patch (for the flood-probability overlay) and weighted surge per cell.
    weights = member_weights(meta)
    np.save(out / "rain_at_landfall.npy", np.stack([r["rain_lf"] for r in results]))
    pd.DataFrame(
        {
            "patch": range(len(uniq)),
            "district_lgd": [k[0] for k in uniq],
            "h3": [k[1] for k in uniq],
        }
    ).to_parquet(out / "patches.parquet", index=False)
    n_cand = len(sg.index.cell_rc)
    p_surge, depth_max, onset_w = np.zeros(n_cand), np.zeros(n_cand), np.zeros(n_cand)
    for r, wt in zip(results, weights, strict=True):
        cells, depth, onset = r["surge"]
        p_surge[cells] += wt
        depth_max[cells] = np.maximum(depth_max[cells], depth)
        onset_w[cells] += wt * np.where(np.isfinite(onset), onset, 0.0)
    hit = np.nonzero(p_surge > 0)[0]
    pd.DataFrame(
        {
            "row": sg.index.cell_rc[hit, 0],
            "col": sg.index.cell_rc[hit, 1],
            "p": p_surge[hit],
            "depth_max_m": depth_max[hit],
            "onset_h_mean": onset_w[hit] / p_surge[hit],
        }
    ).to_parquet(out / "surge_cells.parquet", index=False)
    fac.drop(columns=[c for c in fac.columns if c == "hull"]).to_parquet(out / "facilities.parquet")
    settle[
        ["settlement_id", "population", "node_id", "district_lgd", "unsnapped", "geometry"]
    ].to_parquet(out / "settlements.parquet")
    try:
        code_sha = subprocess.run(
            ["git", "rev-parse", "HEAD"], check=False, cwd=ROOT, capture_output=True, text=True
        ).stdout.strip()
    except OSError:
        code_sha = "unknown"
    run_meta = {
        "run_id": args.run,
        "storm_id": args.storm,
        "created_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "code_sha": code_sha,
        "imd_bulletin_no": reading["bulletin_no"],
        "issued_at_utc": issued.isoformat(),
        "now_utc": now.isoformat(),
        "landfall_utc": (now + pd.Timedelta(hours=landfall_h)).isoformat(),
        "landfall_h": landfall_h,
        "horizon_h": horizon_h,
        "members": counts,
        "runs_used": used,
        "build_dir": str(build_dir.relative_to(ROOT)),
        "rain_needs_review": dr.needs_review,
        "rain_phrases_used": dr.phrases_used,
        "imd_surge_guidance_m": surge_m0,
        "alignment": align_report.per_source if align_report else {},
        "facility_isolation_definition": "cut off from the referral tier (ENGINE §7 referral runs)",
        "max_members": args.max_members,
        "grid_transform": list(sg.transform)[:6],
        "grid_shape": list(sg.shape),
        "patch_h3_res": PATCH_H3_RES,
    }
    (out / "run_meta.json").write_text(json.dumps(run_meta, indent=2, default=str))
    digest = hashlib.sha256((out / "b_settle.npy").read_bytes()).hexdigest()[:16]
    print(f"wrote {out.relative_to(ROOT)} in {time.time() - t0:.0f} s (b_settle sha256 {digest})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
