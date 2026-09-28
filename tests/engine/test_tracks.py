from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from aurora_engine.geo import haversine_km
from aurora_engine.tracks import (
    TRACK_COLUMNS,
    align_to_imd,
    interpolate_hourly,
    match_members,
    read_ecmwf_tc_bufr,
    read_weatherlab_csv,
)

T0 = pd.Timestamp("2025-10-25T12:00:00Z")
ROOT = Path(__file__).resolve().parents[2]


def track(
    source: str, member: int, points: list[tuple[float, float, float, float]]
) -> pd.DataFrame:
    """points: (lead_h, lat, lon, vmax_ms)"""
    return pd.DataFrame(
        {
            "source": source,
            "member_no": member,
            "init_utc": T0,
            "valid_utc": [T0 + pd.Timedelta(hours=p[0]) for p in points],
            "lead_h": [p[0] for p in points],
            "lat": [p[1] for p in points],
            "lon": [p[2] for p in points],
            "vmax_ms": [p[3] for p in points],
            "pmin_hpa": np.nan,
            "rmw_km": np.nan,
        }
    )[TRACK_COLUMNS]


IMD = track("IMD", 0, [(0, 10.0, 88.0, 12.0), (24, 12.0, 86.0, 20.0), (48, 14.0, 84.0, 25.0)])


def test_match_keeps_members_within_300km() -> None:
    near = track("ECMWF", 1, [(0, 11.0, 88.0, 12.0), (24, 13.0, 86.0, 18.0)])  # ~111 km
    far = track("ECMWF", 2, [(0, 14.0, 88.0, 12.0), (24, 16.0, 86.0, 18.0)])  # ~445 km
    kept = match_members(pd.concat([near, far]), IMD)
    assert sorted(kept["member_no"].unique()) == [1]


def test_match_compares_at_the_later_start_time() -> None:
    # Member starts 6 h before IMD; at IMD's first time it is at the IMD position.
    early = track("WNX", 3, [(-6, 5.0, 95.0, 10.0), (0, 10.0, 88.0, 12.0), (24, 12.0, 86.0, 18.0)])
    assert len(match_members(early, IMD)) == len(early)


def test_match_drops_members_that_end_before_imd_starts() -> None:
    gone = track("WNX", 4, [(-24, 10.0, 88.0, 10.0), (-12, 10.0, 88.0, 10.0)])
    assert match_members(gone, IMD).empty


def test_interpolate_hourly_is_linear_and_hourly() -> None:
    hourly = interpolate_hourly(IMD)
    assert len(hourly) == 49
    assert (hourly["valid_utc"].diff().dropna() == pd.Timedelta(hours=1)).all()
    mid = hourly[hourly["valid_utc"] == T0 + pd.Timedelta(hours=12)].iloc[0]
    assert mid["lat"] == pytest.approx(11.0)
    assert mid["vmax_ms"] == pytest.approx(16.0)


def test_alignment_centres_each_source_on_imd() -> None:
    members = pd.concat(
        [
            track("WNX", m, [(0, 10.0 + d, 88.5, 10.0 + m), (48, 14.0 + d, 84.5, 20.0 + m)])
            for m, d in enumerate([-0.5, 0.0, 0.5])
        ]
    )
    aligned, report = align_to_imd(interpolate_hourly(members), interpolate_hourly(IMD))
    imd_h = interpolate_hourly(IMD).set_index("valid_utc")
    stats = aligned.groupby("valid_utc").agg(
        lat=("lat", "mean"), lon=("lon", "mean"), v=("vmax_ms", "median")
    )
    common = stats.index.intersection(imd_h.index)
    assert np.allclose(stats.loc[common, "lat"], imd_h.loc[common, "lat"])
    assert np.allclose(stats.loc[common, "lon"], imd_h.loc[common, "lon"])
    assert np.allclose(stats.loc[common, "v"], imd_h.loc[common, "vmax_ms"])
    # Spread is preserved: the members stay 0.5 degrees apart.
    t = T0 + pd.Timedelta(hours=24)
    lats = aligned[aligned["valid_utc"] == t].sort_values("member_no")["lat"].to_numpy()
    assert np.allclose(np.diff(lats), 0.5)
    assert report.per_source["WNX"]["hours_aligned"] == 49


def test_alignment_tapers_to_zero_24h_beyond_imd_horizon() -> None:
    member = track("ECMWF", 1, [(0, 10.5, 88.0, 12.0), (96, 18.5, 80.0, 20.0)])
    aligned, _ = align_to_imd(interpolate_hourly(member), interpolate_hourly(IMD))
    raw = interpolate_hourly(member).set_index("valid_utc")
    out = aligned.set_index("valid_utc")
    horizon = T0 + pd.Timedelta(hours=48)
    shift_at = lambda h: float(  # noqa: E731
        haversine_km(
            raw.loc[horizon + pd.Timedelta(hours=h), "lat"],
            raw.loc[horizon + pd.Timedelta(hours=h), "lon"],
            out.loc[horizon + pd.Timedelta(hours=h), "lat"],
            out.loc[horizon + pd.Timedelta(hours=h), "lon"],
        )
    )
    assert shift_at(0) > 10
    assert shift_at(12) == pytest.approx(shift_at(0) / 2, rel=0.05)
    assert shift_at(24) == pytest.approx(0, abs=1e-6)
    assert shift_at(36) == pytest.approx(0, abs=1e-6)


def test_weatherlab_reader(tmp_path: Path) -> None:
    csv = tmp_path / "wl.csv"
    csv.write_text(
        "# licence header\n"
        "init_time,track_id,sample,valid_time,lead_time,lat,lon,minimum_sea_level_pressure_hpa,"
        "maximum_sustained_wind_speed_knots,radius_of_maximum_winds_km\n"
        "2025-10-26,IO942025,0.0,2025-10-26 00:00:00,0 days,11.2,87.5,996,29.0,111\n"
        "2025-10-26,IO942025,0.0,2025-10-26 06:00:00,0 days 06:00:00,10.99,87.16,998.8,33.4,112\n"
        "2025-10-26,AL132025,0.0,2025-10-26 00:00:00,0 days,16.5,-75.7,971,90,28\n"
    )
    df = read_weatherlab_csv(csv, "WNX_LARGE", "IO942025")
    assert list(df.columns) == TRACK_COLUMNS
    assert len(df) == 2
    assert df["lead_h"].tolist() == [0.0, 6.0]
    assert df["vmax_ms"].iloc[0] == pytest.approx(29.0 * 1852 / 3600)
    assert str(df["valid_utc"].dt.tz) == "UTC"


ECMWF_SAMPLE = ROOT / "data/raw/ecmwf/ifs_enfo_tf/20251027000000-240h-enfo-tf.bufr"


@pytest.mark.skipif(
    not ECMWF_SAMPLE.exists(), reason="raw ECMWF data not downloaded (make download)"
)
def test_ecmwf_reader_finds_montha_as_03b() -> None:
    df = read_ecmwf_tc_bufr(ECMWF_SAMPLE)
    montha = df[df["storm_id"] == "03B"]
    assert montha["member_no"].nunique() >= 50
    first = montha[montha["lead_h"] == 0]
    assert first["lat"].between(10, 15).all()
    assert first["lon"].between(83, 88).all()
    # Late-lead winds drop to a few m/s as the remnant low decays over land.
    assert montha["vmax_ms"].dropna().between(0, 90).all()
    assert first["vmax_ms"].max() > 10


def test_match_separates_storms_sharing_member_numbers() -> None:
    a = track("ECMWF", 1, [(0, 10.2, 88.0, 12.0), (24, 12.2, 86.0, 18.0)]).assign(storm_id="71B")
    b = track("ECMWF", 1, [(0, 16.0, 66.0, 12.0), (24, 17.0, 65.0, 18.0)]).assign(storm_id="70A")
    kept = match_members(pd.concat([a, b]), IMD)
    assert kept["storm_id"].unique().tolist() == ["71B"]
    assert len(kept) == 2


def test_match_keeps_closest_vortex_per_member() -> None:
    near = track("ECMWF", 1, [(0, 10.1, 88.0, 12.0), (24, 12.1, 86.0, 18.0)]).assign(storm_id="72B")
    nearish = track("ECMWF", 1, [(0, 11.5, 88.0, 12.0), (24, 13.5, 86.0, 18.0)]).assign(
        storm_id="73B"
    )
    kept = match_members(pd.concat([near, nearish]), IMD)
    assert kept["storm_id"].unique().tolist() == ["72B"]
