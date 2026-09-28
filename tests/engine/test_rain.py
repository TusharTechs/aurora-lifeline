from datetime import UTC, date, datetime

import numpy as np
import pandas as pd
import pytest

from aurora_engine.rain import (
    closest_approach_rank,
    cumulative_from_daily,
    daily_rain,
    first_hour_reaching,
    match_districts,
    parse_days,
    patch_daily_totals,
    rain_threshold_mm,
)

DISTRICTS = pd.DataFrame(
    [
        ("Kakinada", "", "Coastal Andhra Pradesh & Yanam", "north_coastal"),
        ("Krishna district", "Krishna", "Coastal Andhra Pradesh & Yanam", "south_coastal"),
        ("Tirupati", "", "Rayalaseema", "rayalaseema"),
        (
            "East Godavari",
            "East & West Godavari",
            "Coastal Andhra Pradesh & Yanam",
            "north_coastal",
        ),
    ],
    columns=["name", "name_variants", "imd_subdivision", "imd_region"],
)
STATE = "Andhra Pradesh"


def w(area: str, day: str, cat: str, cov: str) -> dict[str, str]:
    return {"area_text": area, "date_text": day, "category": cat, "coverage": cov}


def test_parse_days() -> None:
    assert parse_days("26th to 29th October", 2025, 10) == [
        date(2025, 10, d) for d in (26, 27, 28, 29)
    ]
    assert parse_days("28th & 29th October", 2025, 10) == [date(2025, 10, 28), date(2025, 10, 29)]
    assert parse_days("27th", 2025, 10) == [date(2025, 10, 27)]


def test_match_districts_regions_and_names() -> None:
    assert match_districts("Andhra Pradesh & Yanam of Puducherry", DISTRICTS, STATE) == set(
        DISTRICTS.name
    )
    assert match_districts("coastal Andhra Pradesh & Yanam", DISTRICTS, STATE) == {
        "Kakinada",
        "Krishna district",
        "East Godavari",
    }
    assert match_districts("north coastal Andhra Pradesh", DISTRICTS, STATE) == {
        "Kakinada",
        "East Godavari",
    }
    assert match_districts("Rayalaseema", DISTRICTS, STATE) == {"Tirupati"}
    assert match_districts("Kakinada and Krishna", DISTRICTS, STATE) == {
        "Kakinada",
        "Krishna district",
    }
    assert match_districts("Telangana", DISTRICTS, STATE) is None


def test_daily_rain_keeps_coverage_fractions() -> None:
    d = daily_rain(
        [
            w(STATE, "28th", "heavy_to_very_heavy", "a_few"),
            w(STATE, "28th", "extremely_heavy", "isolated"),
            w("Telangana", "28th", "heavy", "many"),
        ],
        DISTRICTS,
        STATE,
        2025,
        10,
    )
    k = d.table[d.table.district == "Kakinada"].set_index("category")["coverage_frac"]
    assert k["heavy_to_very_heavy"] == pytest.approx(0.38)
    assert k["extremely_heavy"] == pytest.approx(0.125)
    assert not d.needs_review


def test_unmatched_area_sets_needs_review() -> None:
    assert daily_rain(
        [w("somewhere vague", "28th", "heavy", "many")], DISTRICTS, STATE, 2025, 10
    ).needs_review


def test_patch_totals_follow_coverage_and_nest() -> None:
    d = daily_rain(
        [
            w(STATE, "28th", "heavy_to_very_heavy", "a_few"),
            w(STATE, "28th", "extremely_heavy", "isolated"),
        ],
        DISTRICTS,
        STATE,
        2025,
        10,
    )
    rows = d.table[d.table.district == "Kakinada"]
    tot = patch_daily_totals(rows, [date(2025, 10, 28)], 20_000, q=1.0, seed_key="m1")[0]
    # One seed; tolerance about 4 sigma for 20,000 patches (sampling is unbiased across seeds).
    assert (tot == 300.0).mean() == pytest.approx(0.125, abs=0.012)  # extremely heavy, q = 1
    assert (tot == 204.4).mean() == pytest.approx(0.38 - 0.125, abs=0.015)  # the rest of the 38%
    assert (tot == 0).mean() == pytest.approx(0.62, abs=0.015)
    again = patch_daily_totals(rows, [date(2025, 10, 28)], 20_000, q=1.0, seed_key="m1")[0]
    assert np.array_equal(tot, again)  # deterministic
    other = patch_daily_totals(rows, [date(2025, 10, 28)], 20_000, q=1.0, seed_key="m2")[0]
    assert not np.array_equal(tot, other)  # members differ


def test_member_rank_and_cumulative_rain() -> None:
    q = closest_approach_rank(np.array([10.0, 50.0, 30.0]))
    assert q.tolist() == [1.0, 0.0, 0.5]
    now = datetime(
        2025, 10, 28, 0, 0, tzinfo=UTC
    )  # 05:30 IST; the IMD day starts 08:30 IST = 03:00 UTC
    r = cumulative_from_daily(np.array([[115.5, 0.0]]), [date(2025, 10, 28)], now, 30)
    assert r.shape == (2, 31)
    assert r[0, 3] == 0.0
    assert r[0, 4] == pytest.approx(115.5 / 24)
    assert r[0, 27] == pytest.approx(115.5)
    assert np.all(np.diff(r[0]) >= 0)
    assert np.all(r[1] == 0)


def test_rain_threshold_and_closure_hour() -> None:
    thr = rain_threshold_mm(np.array([0.0, 1.0, 4.8, np.nan]))
    assert thr[0] == pytest.approx(65.0)  # 50 + 0.3 / 0.02
    assert thr[1] == pytest.approx(115.0)
    assert np.isinf(thr[2]) and np.isinf(thr[3])  # 4.8 + 0.3 >= h_max
    assert rain_threshold_mm(np.array([0.0]), 0.6)[0] == pytest.approx(95.0)
    hours = first_hour_reaching(np.array([0.0, 40.0, 80.0, 120.0]), thr)
    assert hours.tolist()[:2] == [2.0, 3.0]
    assert np.isinf(hours[2])
