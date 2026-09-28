"""Aggregates a storm run into district scenario JSON and a run manifest (BUILD_PLAN 2.7-min).

Reads data/runs/<run_id>/ (from storm_run) and writes, per region district,
data/runs/<run_id>/districts/<lgd>.json valid against schemas/district_scenario.json, plus
data/runs/<run_id>/manifest.json valid against schemas/run_manifest.json.

Member weights (HANDOFF D15): every ensemble source gets equal weight, split equally among its
members. IMD member 0 is the deterministic reference and is reported separately, not blended.

Usage:
    python -m aurora_pipelines.publish --storm montha_2025 --run montha_2025_b21
"""

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import geopandas as gpd
import numpy as np
import pandas as pd
import yaml
from jsonschema import Draft7Validator, FormatChecker
from scipy.spatial import cKDTree

from aurora_engine.facilities import HOSPITAL_TYPES
from aurora_engine.reach import weighted_quantiles
from aurora_engine.weights import member_weights

ROOT = Path(__file__).resolve().parents[2]
DECILES = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9])
ACTION_LEAD_H = {"stage_machine": 6}  # deadline = P10 closure - lead (ENGINE §9)
ACTION_MIN_P = 0.2  # floor on P(crossing closed by landfall) for staging actions (PRIOR)
PRIOR_PARAMS = [
    "rain_k_m_per_mm",
    "rain_r0_mm",
    "rain_h_max_m",
    "rain_coverage_fractions",
    "rain_patch_h3_res6",
    "road_formation_allowance",
    "close_depth_0.3m",
    "surge_decay_0.083m_per_km",
    "surge_sigma_2rm",
    "surge_timing_rm_plus_50km",
    "holland_b_1.5",
    "district_buffer_30km",
    "settlement_min_pop_25",
    "publication_delays",
    "source_balanced_weights",
]


def iso(now: pd.Timestamp, h: float) -> str | None:
    if not np.isfinite(h):
        return None
    return (now + pd.Timedelta(hours=float(h))).strftime("%Y-%m-%dT%H:%M:%SZ")


def isolation_stats(b: np.ndarray, w: np.ndarray, landfall_h: float) -> dict[str, Any]:
    """Probability of isolation by landfall and time quantiles for one node across members."""
    routed = ~np.isneginf(b)
    if not routed.any() or w[routed].sum() == 0:
        return {"p": None, "dec": [None] * 9, "no_route": True, "never": False}
    wr = w[routed] / w[routed].sum()
    br = b[routed]
    p = float((wr * (br <= landfall_h)).sum())
    finite = np.isfinite(br)
    dec = (
        weighted_quantiles(br[finite], wr[finite], DECILES) if finite.any() else np.full(9, np.nan)
    )
    # Deciles are over members where the node is isolated at some point; blank when that share
    # is under 10% (the decile would describe too few members to mean anything).
    if wr[finite].sum() < 0.1:
        dec = np.full(9, np.nan)
    return {
        "p": p,
        "dec": [float(x) if np.isfinite(x) else None for x in dec],
        "no_route": False,
        "never": bool(wr[~finite].sum() >= 0.9),
    }


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _site_labeller(osm_dir: Path, edges: pd.DataFrame) -> Any:
    """Returns edge index -> site dict (road name from OSM, nearest named place within 10 km)."""
    names = pd.read_parquet(osm_dir / "roads.parquet", columns=["way_id", "name"])
    name_by_way = dict(zip(names["way_id"], names["name"], strict=True))
    places = gpd.read_parquet(osm_dir / "places.parquet")
    kx = 111.32 * np.cos(np.radians(16.5))  # km per degree of longitude at the region's latitude
    pts = np.c_[places.geometry.x.to_numpy() * kx, places.geometry.y.to_numpy() * 110.57]
    tree = cKDTree(pts)

    def opt(v: object) -> str | None:
        return str(v) if isinstance(v, str) and v else None

    def site(e: int) -> dict[str, Any]:
        row = edges.iloc[e]
        lon, lat = float(row["mid_lon"]), float(row["mid_lat"])
        dist, i = tree.query([lon * kx, lat * 110.57])
        near = None
        if dist <= 10.0:
            p = places.iloc[int(i)]
            near = {
                "name": opt(p["name_en"]) or str(p["name"]),
                "name_te": opt(p["name_te"]),
                "name_hi": opt(p["name_hi"]),
                "name_or": opt(p["name_or"]),
                "distance_km": round(float(dist), 1),
            }
        return {
            "lat": round(lat, 5),
            "lon": round(lon, 5),
            "crossing_type": opt(row["crossing_type"]),
            "road_class": opt(row["road_class"]),
            "road_name": opt(name_by_way.get(row["osm_way_id"])),
            "near_place": near,
        }

    return site


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--storm", required=True)
    ap.add_argument("--run", required=True)
    args = ap.parse_args()
    run = ROOT / "data/runs" / args.run
    meta = json.loads((run / "run_meta.json").read_text())
    storm = yaml.safe_load((ROOT / f"config/storms/{args.storm}.yaml").read_text())
    run_cfg = next(r for r in storm["runs"] if r["run_id"] == args.run)
    reading = json.loads((ROOT / run_cfg["bulletin"]["reading"]).read_text())
    build = ROOT / meta["build_dir"]
    districts = pd.read_parquet(build / "districts.parquet")
    members = pd.read_parquet(run / "members.parquet")
    w = member_weights(members)
    imd = (members["source"] == "IMD").to_numpy()
    b_set = np.load(run / "b_settle.npy").astype(np.float64)
    b_any = np.load(run / "b_fac_any.npy").astype(np.float64)
    b_ref = np.load(run / "b_fac_ref.npy").astype(np.float64)
    fac = gpd.read_parquet(run / "facilities.parquet")
    st = gpd.read_parquet(run / "settlements.parquet")
    fac_lat, fac_lon = fac.geometry.y.to_numpy(), fac.geometry.x.to_numpy()
    ce = np.load(run / "edge_closures.npz")
    edges = pd.read_parquet(
        build / "edges.parquet",
        columns=[
            "edge_id",
            "osm_way_id",
            "crossing_type",
            "road_class",
            "mid_lon",
            "mid_lat",
            "u",
            "v",
        ],
    )
    osm_dir = json.loads((build / "build_manifest.json").read_text())["inputs"]["osm_extract_dir"]
    site_of = _site_labeller(ROOT / osm_dir / build.name, edges)
    now = pd.Timestamp(meta["now_utc"])
    landfall_h = float(meta["landfall_h"])
    horizon = int(meta["horizon_h"])
    hours = np.arange(0, horizon + 1)
    sources = [s for s in members["source"].unique() if s != "IMD"]
    mode = "ensemble" if sources else "deterministic"

    # Per-member closure hour matrix is sparse: (member, edge) -> hour.
    me, hr = ce["member_edge"], ce["hour"]
    closed = pd.DataFrame({"m": me[:, 0], "e": me[:, 1], "h": hr})

    schema = json.loads((ROOT / "schemas/district_scenario.json").read_text())
    validator = Draft7Validator(schema, format_checker=FormatChecker())
    out_dir = run / "districts"
    out_dir.mkdir(exist_ok=True)
    outputs = []
    for d in districts.itertuples():
        code, name = str(d.osm_relation_id), str(d.name)
        s_sel = (st["district_lgd"] == code).to_numpy()
        pop = st["population"].to_numpy()[s_sel]
        bs = b_set[:, s_sel]
        routed = ~np.isneginf(bs)
        # People cut off from any public hospital by hour t, per member.
        pop_cut = np.stack(
            [((bs <= t) & routed).astype(float) @ pop for t in hours], axis=1
        )  # members x hours
        ens = ~imd

        def q3(x: np.ndarray, _ens: np.ndarray = ens) -> list[float]:
            return (
                [float(v) for v in weighted_quantiles(x[_ens], w[_ens], np.array([0.1, 0.5, 0.9]))]
                if _ens.any()
                else [float(x[imd][0])] * 3
            )

        # Facilities in the district (public tiers + shelters).
        f_sel = (fac["district_lgd"] == code).to_numpy()
        fac_d = fac[f_sel].reset_index(drop=True)
        fac_idx = np.nonzero(f_sel)[0]
        rows, fac_iso_by_member = [], []
        for j, fr in zip(fac_idx, fac_d.itertuples(), strict=True):
            use_ref = fr.type in ("phc", "chc", "sdh_area_hospital")
            b = b_ref[:, j] if use_ref else b_any[:, j]
            stt = isolation_stats(
                b[~imd] if sources else b, w[~imd] if sources else np.ones(1), landfall_h
            )
            by_src = {}
            for s in sources:
                sel = (members["source"] == s).to_numpy()
                bb = b[sel]
                ok = ~np.isneginf(bb)
                if ok.any():
                    by_src[s] = float(np.mean(bb[ok] <= landfall_h))
            fac_iso_by_member.append((b <= landfall_h) & ~np.isneginf(b))
            badges = ["prior"]
            if fr.type == "phc":
                badges.append("possible delivery point")
            if use_ref:
                badges.append("referral isolation")
            if stt["no_route"]:
                badges.append("no mapped route (possible OSM gap)")
            dec = stt["dec"]
            rows.append(
                {
                    "facility_id": fr.facility_id,
                    "type": fr.type,
                    "name": fr.name,
                    "lat": round(float(fac_lat[j]), 6),
                    "lon": round(float(fac_lon[j]), 6),
                    "is_simulated": bool(fr.is_simulated),
                    "p_isolated_by_landfall": None if mode == "deterministic" else stt["p"],
                    "p_isolated_by_source": by_src,
                    "t10": iso(now, dec[0]) if dec[0] is not None else None,
                    "t50": iso(now, dec[4]) if dec[4] is not None else None,
                    "t90": iso(now, dec[8]) if dec[8] is not None else None,
                    "iso_deciles": [iso(now, x) if x is not None else None for x in dec],
                    "referral_p_isolated": stt["p"] if use_ref and mode == "ensemble" else None,
                    "power": {"p": None, "class": None},
                    "expected_births_window": {"p10": None, "p50": None, "p90": None},
                    "badges": badges,
                }
            )
        fac_iso = (
            np.stack(fac_iso_by_member, axis=1)
            if fac_iso_by_member
            else np.zeros((len(members), 0), dtype=bool)
        )
        public = np.isin(fac_d["type"].to_numpy(), HOSPITAL_TYPES)
        n_fac_iso = (
            fac_iso[:, public].sum(axis=1).astype(float) if public.any() else np.zeros(len(members))
        )
        hourly = []
        for i, t in enumerate(hours):
            pc = q3(pop_cut[:, i])
            fac_t = (
                [
                    round(v)
                    for v in q3(
                        np.stack([(b_ref[:, fac_idx][:, public] <= t).sum(1)]).ravel().astype(float)
                    )
                ]
                if public.any()
                else [0, 0, 0]
            )
            hourly.append(
                {
                    "t_utc": iso(now, float(t)),
                    "pop_cut_p10": round(pc[0]),
                    "pop_cut_p50": round(pc[1]),
                    "pop_cut_p90": round(pc[2]),
                    "pop_power_risk_p50": None,
                    "facilities_at_risk": fac_t[1],
                }
            )
        li = int(np.clip(round(landfall_h), 0, horizon))
        head_pop = q3(pop_cut[:, li])
        head_fac = q3(n_fac_iso)
        # Actions (G1 scope): stage machines at crossings likely to close, ranked by people nearby
        # who are cut off in at least half the weighted members (a criticality proxy; ENGINE §7
        # pred-based
        # criticality follows after G1).
        cross = edges["crossing_type"].isin(["bridge", "culvert", "ford"]).to_numpy()
        e_mid = edges[["mid_lon", "mid_lat"]].to_numpy()
        ens_w = w / w.sum() if w.sum() > 0 else np.ones(len(members)) / len(members)
        cl = closed[closed["h"] <= landfall_h]
        p_close = np.zeros(len(edges))
        np.add.at(p_close, cl["e"].to_numpy(), ens_w[cl["m"].to_numpy()])
        cand = np.nonzero(cross & (p_close >= ACTION_MIN_P))[0]
        s_xy = (
            np.c_[st.geometry.x.to_numpy()[s_sel], st.geometry.y.to_numpy()[s_sel]]
            if s_sel.any()
            else np.zeros((0, 2))
        )
        p_cut_set = (
            ((bs <= landfall_h) & routed).astype(float).T @ ens_w if s_sel.any() else np.zeros(0)
        )
        scored: list[tuple[float, float, int]] = []
        for cand_e in cand:
            ce_i = int(cand_e)
            near_s = (
                np.hypot(
                    (s_xy[:, 0] - e_mid[ce_i, 0]) * 106.5, (s_xy[:, 1] - e_mid[ce_i, 1]) * 111.2
                )
                <= 5.0
            )
            people = float(
                (pop[near_s] * p_cut_set[near_s]).sum()
            )  # expected people cut off nearby
            if people >= 1:
                scored.append((float(people * p_close[ce_i]), people, ce_i))
        scored.sort(reverse=True)
        actions = []
        # One action per site: skip crossings within 1 km of a higher-ranked one.
        picked: list[tuple[float, float, int]] = []
        for item in scored:
            site = item[2]
            if all(
                np.hypot(
                    (e_mid[site, 0] - e_mid[q, 0]) * 106.5, (e_mid[site, 1] - e_mid[q, 1]) * 111.2
                )
                > 1.0
                for _, _, q in picked
            ):
                picked.append(item)
            if len(picked) == 25:
                break
        for _, people, e in picked:
            hh = closed.loc[closed["e"] == e]
            t10 = float(
                weighted_quantiles(hh["h"].to_numpy(), ens_w[hh["m"].to_numpy()], np.array([0.1]))[
                    0
                ]
            )
            actions.append(
                {
                    "action_id": f"stage_{e}",
                    "type": "stage_machine",
                    "target_id": f"edge_{e}",
                    "deadline_utc": iso(now, max(t10 - ACTION_LEAD_H["stage_machine"], 0.0)),
                    "deadline_basis": "P10 closure - 6 h",
                    "people_protected": round(people),
                    "p_event": round(float(p_close[e]), 3),
                    "rank": 0,
                    "evidence_ref": f"{args.run}/edge_closures.npz#edge={e}",
                    "site": site_of(e),
                }
            )
        # ``picked`` is already ordered by people protected x P(event) (ENGINE §9).
        actions = actions[:25]
        for r, a in enumerate(actions, start=1):
            a["rank"] = r
        doc = {
            "schema_version": "1",
            "run_id": args.run,
            "storm_id": args.storm,
            "storm_status": storm["status"],
            "district_lgd": code,
            "district_name": name,
            "provenance": {
                "imd_bulletin_no": reading["bulletin_no"],
                "imd_issued_at_utc": pd.Timestamp(reading["issued_at_utc"]).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
                "landfall_window_text": reading["landfall"]["window_text"]
                if reading.get("landfall")
                else None,
                "members": {k: int(v) for k, v in meta["members"].items()},
                "mode": mode,
                "data_versions": {
                    "osm": "geofabrik southern-zone 2026-09-27",
                    "population": "WorldPop 2020 constrained",
                    "dem": "Copernicus GLO-30",
                    "hand": "AURORA 90 m from GLO-30",
                    "water": "JRC GSW 1.4",
                },
                "code_sha": meta["code_sha"],
                "model_ids": {},
            },
            "time_axis": {
                "now_utc": iso(now, 0.0),
                "landfall_utc": iso(now, landfall_h),
                "step_h": 1,
                "n_steps": horizon,
            },
            "headline": {
                "pop_cut_hospital": {
                    "p10": round(head_pop[0]),
                    "p50": round(head_pop[1]),
                    "p90": round(head_pop[2]),
                },
                "facilities_at_risk": {
                    "p10": round(head_fac[0]),
                    "p50": round(head_fac[1]),
                    "p90": round(head_fac[2]),
                },
                "pop_served_by_substations_at_risk": {
                    "p10": None,
                    "p50": None,
                    "p90": None,
                    "class": None,
                },
                "at": "landfall",
            },
            "hourly": hourly,
            "facilities": rows,
            "actions": actions,
            "completeness": {
                "badge": "partial",
                "phc_ratio": None,
                "chc_ratio": None,
                "substations_mapped": 0,
            },
            "tiles": {
                "url_template": f"/tiles/{args.run}/{{layer}}/{{z}}/{{x}}/{{y}}.pbf",
                "layers": ["edges", "settlements", "facilities", "surge", "flood", "tracks"],
                "minzoom": 6,
                "maxzoom": 14,
            },
            "flags": {
                "needs_review": bool(meta["rain_needs_review"]),
                "screening_surge": True,
                "prior_params": PRIOR_PARAMS,
            },
        }
        errs = sorted(validator.iter_errors(doc), key=lambda e: list(e.path))
        if errs:
            raise SystemExit(
                f"{name}: invalid district JSON: "
                + "; ".join(f"{list(e.path)}: {e.message}" for e in errs[:5])
            )
        path = out_dir / f"{code}.json"
        path.write_text(json.dumps(doc, separators=(",", ":")))
        outputs.append(path)
        print(
            f"{name:18} people cut off from any public hospital by landfall P10/P50/P90 = "
            f"{head_pop[0]:>9,.0f} / {head_pop[1]:>9,.0f} / {head_pop[2]:>9,.0f}; "
            f"facilities at risk P50 {head_fac[1]:.0f}; actions {len(actions)}; "
            f"{path.stat().st_size / 1024:.0f} KB"
        )

    # District outlines for CAP <area><polygon> only (never rendered on the map), <= 100 points.
    areas = {}
    for code, geom in zip(
        gpd.read_parquet(build / "districts.parquet")["osm_relation_id"].astype(str),
        gpd.read_parquet(build / "districts.parquet").geometry,
        strict=True,
    ):
        poly = max(getattr(geom, "geoms", [geom]), key=lambda g: g.area)
        tol = 0.002
        ring = poly.exterior.simplify(tol)
        while len(ring.coords) > 100:
            tol *= 1.5
            ring = poly.exterior.simplify(tol)
        areas[code] = [[round(x, 4), round(y, 4)] for x, y in ring.coords]
    (run / "areas.json").write_text(json.dumps(areas, separators=(",", ":")))

    # Run manifest.
    inputs = [
        {
            "uri": run_cfg["bulletin"]["source_url"],
            "sha256": run_cfg["bulletin"]["sha256"],
            "source": "IMD",
            "issued_at_utc": pd.Timestamp(run_cfg["bulletin"]["issued_at_utc"]).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
        }
    ]
    for src, desc in meta["runs_used"].items():
        init, fname = desc.split(" ", 1)
        cfg = storm["sources"][src]
        p = ROOT / cfg["path"] / fname
        inputs.append(
            {
                "uri": f"{cfg['path']}/{fname}",
                "sha256": sha256(p),
                "source": src,
                "issued_at_utc": pd.Timestamp(init).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "available_at_utc": (
                    pd.Timestamp(init) + pd.Timedelta(hours=float(cfg["publication_delay_h"]))
                ).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
        )
    manifest = {
        "run_id": args.run,
        "storm_id": args.storm,
        "created_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "code_sha": meta["code_sha"] or "unknown",
        "imd_bulletin_no": reading["bulletin_no"],
        "mode": mode,
        "run_label": None,
        "inputs": inputs,
        "members": [
            {"source": str(src), "member_no": int(mn), "weight": float(wt)}
            for src, mn, wt in zip(members["source"], members["member_no"], w, strict=True)
        ],
        "parameters": [
            {
                "name": n,
                "value": None,
                "status": "PRIOR",
                "source": "docs/ENGINE.md; HANDOFF D15, D22",
            }
            for n in PRIOR_PARAMS
        ],
        "models": [],
        "seed": 0,
        "outputs": [
            {"path": str(p.relative_to(run)), "sha256": sha256(p), "bytes": p.stat().st_size}
            for p in outputs
        ],
    }
    m_errs = list(
        Draft7Validator(
            json.loads((ROOT / "schemas/run_manifest.json").read_text()),
            format_checker=FormatChecker(),
        ).iter_errors(manifest)
    )
    if m_errs:
        raise SystemExit("invalid manifest: " + "; ".join(e.message for e in m_errs[:5]))
    (run / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print(
        f"manifest: {len(inputs)} inputs, {len(manifest['members'])} members, "
        f"{len(outputs)} district files"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
