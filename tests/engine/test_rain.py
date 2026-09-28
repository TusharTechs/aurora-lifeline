from datetime import UTC, date, datetime

import numpy as np
import pandas as pd
import pytest

from aurora_engine.rain import (
    closest_approach_rank,
    daily_rain,
    first_hour_reaching,
    hourly_cumulative_mm,
    match_districts,
    parse_days,
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


def test_parse_days() -> None:
    assert parse_days("26th to 29th October", 2025, 10) == [
        date(2025, 10, d) for d in (26, 27, 28, 29)
    ]
    assert parse_days("28th & 29th October", 2025, 10) == [date(2025, 10, 28), date(2025, 10, 29)]
    assert parse_days("27th", 2025, 10) == [date(2025, 10, 27)]


def test_match_districts_regions_and_names() -> None:
    assert match_districts(
        "Andhra Pradesh & Yanam of Puducherry", DISTRICTS, "Andhra Pradesh"
    ) == set(DISTRICTS.name)
    assert match_districts("coastal Andhra Pradesh & Yanam", DISTRICTS, "Andhra Pradesh") == {
        "Kakinada", "Krishna district", "East Godavari"}  # fmt: skip
    assert match_districts("north coastal Andhra Pradesh", DISTRICTS, "Andhra Pradesh") == {
        "Kakinada",
        "East Godavari",
    }
    assert match_districts("Rayalaseema", DISTRICTS, "Andhra Pradesh") == {"Tirupati"}
    assert match_districts("Kakinada and Krishna", DISTRICTS, "Andhra Pradesh") == {
        "Kakinada",
        "Krishna district",
    }
    assert match_districts("Telangana", DISTRICTS, "Andhra Pradesh") is None


def test_isolated_addons_are_ignored_and_highest_category_wins() -> None:
    w = [
        {
            "area_text": "Andhra Pradesh",
            "date_text": "28th",
            "category": "heavy_to_very_heavy",
            "coverage": "a_few",
        },
        {
            "area_text": "Andhra Pradesh",
            "date_text": "28th",
            "category": "extremely_heavy",
            "coverage": "isolated",
        },
        {
            "area_text": "north coastal Andhra Pradesh",
            "date_text": "28th",
            "category": "very_heavy",
            "coverage": "many",
        },
        {"area_text": "Telangana", "date_text": "28th", "category": "heavy", "coverage": "many"},
    ]
    d = daily_rain(w, DISTRICTS, "Andhra Pradesh", 2025, 10)
    t = d.table.set_index("district")
    assert (
        t.loc["Kakinada", "category"] == "very_heavy"
    )  # same upper bound; region clause is not lower
    assert t.loc["Tirupati", "category"] == "heavy_to_very_heavy"
    assert not d.needs_review  # Telangana is another state, not an unmatched phrase


def test_unmatched_area_sets_needs_review() -> None:
    w = [
        {
            "area_text": "somewhere vague",
            "date_text": "28th",
            "category": "heavy",
            "coverage": "many",
        }
    ]
    assert daily_rain(w, DISTRICTS, "Andhra Pradesh", 2025, 10).needs_review


def test_member_rank_and_cumulative_rain() -> None:
    q = closest_approach_rank(np.array([10.0, 50.0, 30.0]))
    assert q.tolist() == [1.0, 0.0, 0.5]
    daily = pd.DataFrame([{"district": "Kakinada", "day": date(2025, 10, 28), "category": "heavy",
                           "lo_mm": 64.5, "hi_mm": 115.5}])  # fmt: skip
    now = datetime(
        2025, 10, 28, 0, 0, tzinfo=UTC
    )  # 05:30 IST; the IMD day starts 08:30 IST = 03:00 UTC
    r = hourly_cumulative_mm(daily, "Kakinada", 1.0, now, 30)
    assert r[3] == 0.0
    assert r[4] == pytest.approx(115.5 / 24)
    assert r[27] == pytest.approx(115.5)
    assert np.all(np.diff(r) >= 0)


def test_rain_threshold_and_closure_hour() -> None:
    thr = rain_threshold_mm(np.array([0.0, 1.0, 4.8, np.nan]))
    assert thr[0] == pytest.approx(65.0)  # 50 + 0.3 / 0.02
    assert thr[1] == pytest.approx(115.0)
    assert np.isinf(thr[2]) and np.isinf(thr[3])  # 4.8 + 0.3 >= h_max
    hours = first_hour_reaching(np.array([0.0, 40.0, 80.0, 120.0]), thr)
    assert hours.tolist()[:2] == [2.0, 3.0]
    assert np.isinf(hours[2])
