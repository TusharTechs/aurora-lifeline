"""Storm tracks: ingest, storm matching, hourly interpolation and alignment to IMD (ENGINE §2).

All tracks share one long-format table (``TRACK_COLUMNS``), one row per member and valid time,
in SI units and UTC. ``IMD/0`` is the official track; ensemble members come from Weather Lab
(WeatherNext) and the ECMWF IFS ensemble. Best tracks are verification labels and never enter here.
"""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from aurora_engine.geo import haversine_km
from aurora_engine.units import KT_TO_MS

TRACK_COLUMNS = [
    "source",
    "member_no",
    "init_utc",
    "valid_utc",
    "lead_h",
    "lat",
    "lon",
    "vmax_ms",
    "pmin_hpa",
    "rmw_km",
]

# Weather Lab model name -> AURORA source key.
WEATHERLAB_SOURCES = {
    "FNV3_LARGE_ENSEMBLE": "WNX_LARGE",
    "FNV3P2": "WNX",
    "OPER": "WNX_OPER",
}

MATCH_RADIUS_KM = 300.0  # SPEC §3: a member belongs to the storm if it starts within 300 km of IMD
ALIGN_TAPER_H = 24.0  # ENGINE §2: alignment tapers to zero over 24 h beyond IMD's horizon


_EPOCH = pd.Timestamp("1970-01-01", tz="UTC")


def _epoch_s(t: "pd.Series | pd.DatetimeIndex | pd.Timestamp") -> np.ndarray:
    """Seconds since the epoch as float, independent of the datetime resolution (s/ms/us/ns)."""
    if isinstance(t, pd.Timestamp):
        return np.asarray([(t - _EPOCH) / pd.Timedelta(seconds=1)], dtype="float64")
    as_dt = pd.DatetimeIndex(pd.to_datetime(t, utc=True))
    return np.asarray((as_dt - _EPOCH) / pd.Timedelta(seconds=1), dtype="float64")


def _empty() -> pd.DataFrame:
    return pd.DataFrame({c: pd.Series(dtype="float64") for c in TRACK_COLUMNS})


def _finalise(df: pd.DataFrame) -> pd.DataFrame:
    df = df[TRACK_COLUMNS].copy()
    df["member_no"] = df["member_no"].astype("int64")
    df["lead_h"] = df["lead_h"].astype("float64")
    for c in ("lat", "lon", "vmax_ms", "pmin_hpa", "rmw_km"):
        df[c] = pd.to_numeric(df[c], errors="coerce").astype("float64")
    for c in ("init_utc", "valid_utc"):
        df[c] = pd.to_datetime(df[c], utc=True)
    return df.sort_values(["source", "member_no", "valid_utc"], kind="stable").reset_index(
        drop=True
    )


# ---------------------------------------------------------------- ingest


def read_weatherlab_csv(path: Path, source: str, track_id: str) -> pd.DataFrame:
    """Reads one Weather Lab "paired" ensemble CSV and returns the members of ``track_id``.

    "Paired" means each forecast track is labelled with the official storm ID it corresponds
    to; the files contain forecast rows only (lead 0 is the model's analysis at init time).
    """
    raw = pd.read_csv(path, comment="#")
    raw = raw[raw["track_id"] == track_id]
    if raw.empty:
        return _empty()
    init = pd.to_datetime(raw["init_time"], utc=True)
    valid = pd.to_datetime(raw["valid_time"], utc=True)
    df = pd.DataFrame(
        {
            "source": source,
            "member_no": raw["sample"].astype("int64"),
            "init_utc": init,
            "valid_utc": valid,
            "lead_h": (valid - init).dt.total_seconds() / 3600.0,
            "lat": raw["lat"],
            "lon": raw["lon"],
            "vmax_ms": raw["maximum_sustained_wind_speed_knots"] * KT_TO_MS,
            "pmin_hpa": raw["minimum_sea_level_pressure_hpa"],
            "rmw_km": raw["radius_of_maximum_winds_km"],
        }
    )
    return _finalise(df)


def _bufr_missing(values: np.ndarray) -> np.ndarray:
    """ecCodes marks missing values with huge sentinels; turn them into NaN."""
    arr = np.asarray(values, dtype="float64")
    return np.where(np.abs(arr) > 1e10, np.nan, arr)


def read_ecmwf_tc_bufr(path: Path, source: str = "ECMWF") -> pd.DataFrame:
    """Reads an ECMWF ensemble tropical-cyclone track BUFR file (``enfo``/``tf``).

    Returns every storm in the file with an extra ``storm_id`` column. Each BUFR message is
    one storm; ensemble members are subsets. Positions are the pressure centre; the wind is
    the maximum 10 m wind (m/s). Layout per ECMWF's ``bufr_read_tropical_cyclone`` example.
    """
    import eccodes as ec  # noqa: PLC0415 - lazy: loads the ecCodes C library only when needed

    frames: list[pd.DataFrame] = []
    with path.open("rb") as fh:
        while (h := ec.codes_bufr_new_from_file(fh)) is not None:
            try:
                ec.codes_set(h, "unpack", 1)
                storm_id = str(ec.codes_get(h, "stormIdentifier")).strip()
                init = pd.Timestamp(
                    year=int(ec.codes_get(h, "year")),
                    month=int(ec.codes_get(h, "month")),
                    day=int(ec.codes_get(h, "day")),
                    hour=int(ec.codes_get(h, "hour")),
                    minute=int(ec.codes_get(h, "minute")),
                    tz="UTC",
                )
                members = np.asarray(ec.codes_get_array(h, "ensembleMemberNumber"), dtype="int64")
                n = len(members)

                def arr(key: str, n: int = n, h: int = h) -> np.ndarray:
                    v = _bufr_missing(ec.codes_get_array(h, key))
                    return np.full(n, v[0]) if v.size == 1 else v

                # Rank 2: storm centre in each member's analysis. Rank 1: observed centre.
                rows = [
                    pd.DataFrame(
                        {
                            "member_no": members,
                            "lead_h": 0.0,
                            "lat": arr("#2#latitude"),
                            "lon": arr("#2#longitude"),
                            "pmin_hpa": arr("#1#pressureReducedToMeanSeaLevel") / 100.0,
                            "vmax_ms": arr("#1#windSpeedAt10M"),
                        }
                    )
                ]
                period = 1
                while True:
                    try:
                        hours = arr(f"#{period}#timePeriod")
                    except ec.KeyValueNotFoundError:
                        break
                    rows.append(
                        pd.DataFrame(
                            {
                                "member_no": members,
                                "lead_h": hours,
                                "lat": arr(f"#{2 * period + 2}#latitude"),
                                "lon": arr(f"#{2 * period + 2}#longitude"),
                                "pmin_hpa": arr(f"#{period + 1}#pressureReducedToMeanSeaLevel")
                                / 100.0,
                                "vmax_ms": arr(f"#{period + 1}#windSpeedAt10M"),
                            }
                        )
                    )
                    period += 1
                df = pd.concat(rows, ignore_index=True).dropna(subset=["lat", "lon", "lead_h"])
                df["source"] = source
                df["init_utc"] = init
                df["valid_utc"] = init + pd.to_timedelta(df["lead_h"], unit="h")
                df["rmw_km"] = np.nan
                df = _finalise(df)
                df["storm_id"] = storm_id
                frames.append(df)
            finally:
                ec.codes_release(h)
    if not frames:
        out = _empty()
        out["storm_id"] = pd.Series(dtype="object")
        return out
    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------------- matching and interpolation


def position_at(track: pd.DataFrame, t: pd.Timestamp) -> tuple[float, float] | None:
    """Linearly interpolated (lat, lon) of a single-member track at time ``t``, or None."""
    times = _epoch_s(track["valid_utc"])
    x = float(_epoch_s(t)[0])
    if track.empty or x < times[0] or x > times[-1]:
        return None
    lat = float(np.interp(x, times, track["lat"].to_numpy()))
    lon = float(np.interp(x, times, track["lon"].to_numpy()))
    return lat, lon


def match_members(
    tracks: pd.DataFrame, imd: pd.DataFrame, radius_km: float = MATCH_RADIUS_KM
) -> pd.DataFrame:
    """Keeps members whose first point lies within ``radius_km`` of IMD at the same valid time.

    The comparison time is the later of the member's first time and IMD's first time, with both
    tracks interpolated there. Members that end before IMD's track starts, or start after it
    ends, are dropped. If ``tracks`` has a ``storm_id`` column (ECMWF files hold several storms
    that share member numbers), each (storm_id, member) track is tested separately and, where one
    member tracks more than one candidate vortex, the closest to IMD is kept.
    """
    imd_sorted = imd.sort_values("valid_utc")
    keys = ["source", "member_no"] + (["storm_id"] if "storm_id" in tracks.columns else [])
    best: dict[tuple[str, int], tuple[float, pd.DataFrame]] = {}
    for _, group in tracks.groupby(keys, sort=True):
        member = group.sort_values("valid_utc")
        t_ref = max(member["valid_utc"].iloc[0], imd_sorted["valid_utc"].iloc[0])
        p_member, p_imd = position_at(member, t_ref), position_at(imd_sorted, t_ref)
        if p_member is None or p_imd is None:
            continue
        dist = float(haversine_km(p_member[0], p_member[1], p_imd[0], p_imd[1]))
        member_key = (str(member["source"].iloc[0]), int(member["member_no"].iloc[0]))
        if dist <= radius_km and (member_key not in best or dist < best[member_key][0]):
            best[member_key] = (dist, member)
    if not best:
        return tracks.iloc[0:0]
    return pd.concat([best[k][1] for k in sorted(best)], ignore_index=True)


def interpolate_hourly(tracks: pd.DataFrame) -> pd.DataFrame:
    """Interpolates every member linearly to whole-hour steps between its first and last point."""
    out = []
    numeric = ["lat", "lon", "vmax_ms", "pmin_hpa", "rmw_km"]
    for (src, mem), group in tracks.groupby(["source", "member_no"], sort=True):
        member = group.sort_values("valid_utc").drop_duplicates("valid_utc")
        start = member["valid_utc"].iloc[0].ceil("h")
        end = member["valid_utc"].iloc[-1].floor("h")
        if end < start:
            continue
        hours = pd.date_range(start, end, freq="h", tz="UTC")
        x = _epoch_s(member["valid_utc"])
        xi = _epoch_s(hours)
        cols: dict[str, object] = {"source": src, "member_no": mem, "valid_utc": hours}
        for c in numeric:
            y = member[c].to_numpy(dtype="float64")
            ok = ~np.isnan(y)
            cols[c] = np.interp(xi, x[ok], y[ok]) if ok.sum() >= 2 else np.full(len(xi), np.nan)
        init = member["init_utc"].iloc[0]
        cols["init_utc"] = init
        cols["lead_h"] = (hours - init).total_seconds() / 3600.0
        out.append(pd.DataFrame(cols))
    return _finalise(pd.concat(out, ignore_index=True)) if out else _empty()


# ---------------------------------------------------------------- alignment


@dataclass(frozen=True)
class AlignmentReport:
    """What alignment did, for the run manifest."""

    per_source: dict[str, dict[str, float]]
    horizon_utc: pd.Timestamp


def align_to_imd(members: pd.DataFrame, imd: pd.DataFrame) -> tuple[pd.DataFrame, AlignmentReport]:
    """Aligns each source's ensemble to the IMD official forecast (ENGINE §2, step 3).

    Both inputs must be hourly (``interpolate_hourly``). For each source and each hour within
    IMD's horizon, every member is translated by (IMD position - source mean position) and its
    intensity scaled so that the source median equals IMD's intensity. Beyond the horizon both
    corrections taper linearly to zero over 24 h. Aligning per source keeps each source's own
    spread while IMD sets the centre, so no source dominates the centre by member count.
    """
    imd_h = imd.set_index("valid_utc").sort_index()
    horizon = imd_h.index.max()
    out = []
    report: dict[str, dict[str, float]] = {}
    for src, group in members.groupby("source", sort=True):
        g = group.copy()
        stats = g.groupby("valid_utc").agg(
            mlat=("lat", "mean"), mlon=("lon", "mean"), mv=("vmax_ms", "median")
        )
        common = stats.index.intersection(imd_h.index)
        corr = pd.DataFrame(index=stats.index, data={"dlat": 0.0, "dlon": 0.0, "vscale": 1.0})
        corr.loc[common, "dlat"] = imd_h.loc[common, "lat"] - stats.loc[common, "mlat"]
        corr.loc[common, "dlon"] = imd_h.loc[common, "lon"] - stats.loc[common, "mlon"]
        with np.errstate(divide="ignore", invalid="ignore"):
            scale = imd_h.loc[common, "vmax_ms"] / stats.loc[common, "mv"]
        corr.loc[common, "vscale"] = scale.where(np.isfinite(scale), 1.0)
        # Taper: hold the last in-horizon correction and fade it to zero over ALIGN_TAPER_H.
        if len(common):
            last = corr.loc[common.max()]
            beyond = corr.index[corr.index > horizon]
            w = np.clip(1.0 - (beyond - horizon).total_seconds() / 3600.0 / ALIGN_TAPER_H, 0.0, 1.0)
            corr.loc[beyond, "dlat"] = last["dlat"] * w
            corr.loc[beyond, "dlon"] = last["dlon"] * w
            corr.loc[beyond, "vscale"] = 1.0 + (last["vscale"] - 1.0) * w
        j = corr.loc[g["valid_utc"]].to_numpy()
        g["lat"] = g["lat"].to_numpy() + j[:, 0]
        g["lon"] = g["lon"].to_numpy() + j[:, 1]
        g["vmax_ms"] = g["vmax_ms"].to_numpy() * j[:, 2]
        out.append(g)
        report[str(src)] = {
            "hours_aligned": float(len(common)),
            "max_shift_km": float(
                np.nanmax(haversine_km(0.0, 0.0, corr["dlat"].to_numpy(), corr["dlon"].to_numpy()))
            )
            if len(corr)
            else 0.0,
            "median_vscale": float(np.nanmedian(corr.loc[common, "vscale"]))
            if len(common)
            else 1.0,
        }
    aligned = pd.concat(out, ignore_index=True) if out else members.iloc[0:0]
    return _finalise(aligned), AlignmentReport(per_source=report, horizon_utc=horizon)
