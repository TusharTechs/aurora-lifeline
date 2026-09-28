"""Rain flooding from IMD rainfall categories and height above nearest drainage (ENGINE §5).

Slice rule (all PRIOR, recorded in the manifest):

1. For each district and IMD day (08:30 IST to 08:30 IST), take the bulletin's category. A warning
   for a subdivision or region applies to all its districts; a warning naming a district overrides
   it. Clauses whose coverage is "isolated" are add-ons and are ignored; the highest remaining
   category wins. No warning means 0 mm. Unmatched text sets ``needs_review``.
2. Member m's daily total = lower + q_m (upper - lower), where q_m in [0, 1] ranks members by
   closest approach to the district centroid (closest = 1). IMD member 0 uses the midpoint.
3. Each daily total is spread evenly over its 24 hours; R(t) is the total since "now".
4. A location floods when HAND < h*(R) = clamp(k (R - R0), 0, h_max); depth = h* - HAND.
   A road closes when that depth exceeds 0.3 m, i.e. when R(t) >= R0 + (HAND + 0.3) / k
   (and HAND + 0.3 < h_max).

Riverine inflow from upstream districts is not modelled in the slice.
"""

import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pandas as pd
from numpy.typing import NDArray

IST = timezone(timedelta(hours=5, minutes=30))

# mm per 24 h (IMD RSMC terminology; the 300 mm cap on extremely heavy is PRIOR).
CATEGORY_MM: dict[str, tuple[float, float]] = {
    "heavy": (64.5, 115.5),
    "heavy_to_very_heavy": (64.5, 204.4),
    "very_heavy": (115.6, 204.4),
    "extremely_heavy": (204.5, 300.0),
}
K_M_PER_MM = 0.02  # PRIOR
R0_MM = 50.0  # PRIOR
H_MAX_M = 5.0  # PRIOR
CLOSE_DEPTH_M = 0.3  # Pregnolato et al. (2017); PRIOR for flowing water

MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august", "september",
     "october", "november", "december"], start=1)}  # fmt: skip


def parse_days(date_text: str, year: int, default_month: int) -> list[date]:
    """'26th to 29th October' -> 26..29 Oct; '28th & 29th October' -> 28, 29; '27th' -> 27."""
    text = date_text.lower()
    month = next((m for name, m in MONTHS.items() if name in text), default_month)
    nums = [int(x) for x in re.findall(r"(\d{1,2})(?:st|nd|rd|th)?", text)]
    if not nums:
        return []
    if re.search(r"\bto\b|-|\u2013", text) and len(nums) >= 2:
        days = list(range(nums[0], nums[1] + 1))
    else:
        days = nums
    return [date(year, month, d) for d in days]


def _norm(s: str) -> str:
    return re.sub(r"[^a-z ]", " ", s.lower()).replace("  ", " ").strip()


def match_districts(area_text: str, districts: pd.DataFrame, state_name: str) -> set[str] | None:
    """District names an IMD area phrase covers; None if it cannot be matched (needs review).

    ``districts`` has columns name, name_variants ('|'-separated), imd_subdivision, imd_region.
    """
    t = _norm(area_text)
    named: set[str] = set()
    for name, variants_text in zip(districts["name"], districts["name_variants"], strict=True):
        variants = [str(name), *[v for v in str(variants_text).split("|") if v]]
        if any(re.search(rf"\b{re.escape(_norm(v))}\b", t) for v in variants if _norm(v)):
            named.add(str(name))
    if named:
        return named
    region_map = {
        "north coastal": districts["imd_region"] == "north_coastal",
        "south coastal": districts["imd_region"] == "south_coastal",
        "rayalaseema": districts["imd_region"] == "rayalaseema",
    }
    for phrase, mask in region_map.items():
        if phrase in t:
            return {str(n) for n in districts.loc[mask, "name"]}
    state = _norm(state_name)
    if "coastal" in t and state in t:
        coastal = districts["imd_subdivision"].str.startswith("Coastal")
        return {str(n) for n in districts.loc[coastal, "name"]}
    if state in t:
        return {str(n) for n in districts["name"]}
    return None


@dataclass
class DailyRain:
    """Daily (lower, upper) mm per district and IMD day, plus review flags."""

    table: pd.DataFrame  # district, day (date), category, lo_mm, hi_mm
    needs_review: bool = False
    phrases_used: list[str] = field(default_factory=list)


def daily_rain(
    warnings: list[dict[str, str]], districts: pd.DataFrame, state_name: str, year: int, month: int
) -> DailyRain:
    """Applies the slice rule (step 1) to a bulletin's rainfall warnings for one state."""
    best: dict[tuple[str, date], str] = {}
    needs_review = False
    used = []
    other_states = {"telangana", "odisha", "tamil nadu", "west bengal", "karnataka", "kerala"}
    for w in warnings:
        if w.get("coverage") == "isolated":
            continue
        cat = w["category"]
        if cat not in CATEGORY_MM:
            needs_review = True
            continue
        covered = match_districts(w["area_text"], districts, state_name)
        if covered is None:
            if not any(o in _norm(w["area_text"]) for o in other_states):
                needs_review = True
            continue
        used.append(f"{w['area_text']} | {w['date_text']} | {cat}")
        for day in parse_days(w["date_text"], year, month):
            for d in covered:
                cur = best.get((d, day))
                # Highest upper bound wins; on a tie, the higher lower bound (more specific).
                if cur is None or CATEGORY_MM[cat][::-1] > CATEGORY_MM[cur][::-1]:
                    best[(d, day)] = cat
    rows = [
        {
            "district": d,
            "day": day,
            "category": c,
            "lo_mm": CATEGORY_MM[c][0],
            "hi_mm": CATEGORY_MM[c][1],
        }
        for (d, day), c in sorted(best.items())
    ]
    cols = ["district", "day", "category", "lo_mm", "hi_mm"]
    return DailyRain(pd.DataFrame(rows, columns=cols), needs_review, used)


def closest_approach_rank(dist_km: NDArray[np.float64]) -> NDArray[np.float64]:
    """q in [0, 1] per member: 1 for the closest approach, 0 for the farthest (ties averaged)."""
    n = len(dist_km)
    if n == 1:
        return np.array([0.5])
    ranks = pd.Series(dist_km).rank(method="average").to_numpy() - 1  # 0 = closest
    return np.asarray(1.0 - ranks / (n - 1))


def hourly_cumulative_mm(
    daily: pd.DataFrame, district: str, q: float, now_utc: datetime, n_hours: int
) -> NDArray[np.float64]:
    """R(t) at hours 0..n_hours after now for one district and member quantile q."""
    rate = np.zeros(n_hours + 1)
    sub = daily[daily["district"] == district]
    hours_utc = [now_utc + timedelta(hours=h) for h in range(n_hours + 1)]
    for rec in sub.to_dict("records"):
        day: date = rec["day"]
        lo, hi = float(rec["lo_mm"]), float(rec["hi_mm"])
        start = datetime(day.year, day.month, day.day, 8, 30, tzinfo=IST)
        end = start + timedelta(days=1)
        total = lo + q * (hi - lo)
        for i, t in enumerate(hours_utc[1:], start=1):
            # rain falling during hour (t-1, t]
            if start < t <= end:
                rate[i] += total / 24.0
    return np.cumsum(rate)


def rain_threshold_mm(hand_m: NDArray[np.float64]) -> NDArray[np.float64]:
    """Cumulative rain at which a point with this HAND floods deeper than 0.3 m (inf if never)."""
    need = hand_m + CLOSE_DEPTH_M
    r = R0_MM + need / K_M_PER_MM
    return np.where(np.isfinite(hand_m) & (need < H_MAX_M), r, np.inf)


def first_hour_reaching(
    cum_mm: NDArray[np.float64], threshold_mm: NDArray[np.float64]
) -> NDArray[np.float64]:
    """First hour index at which cumulative rain reaches each threshold; inf if never."""
    idx = np.searchsorted(cum_mm, threshold_mm, side="left").astype(np.float64)
    idx[idx >= len(cum_mm)] = np.inf
    return idx
