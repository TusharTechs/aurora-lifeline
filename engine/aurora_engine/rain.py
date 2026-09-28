"""Rain flooding from IMD rainfall categories and height above nearest drainage (ENGINE §5).

Slice rule (PRIOR; recorded in the manifest; amended 28 Sep 2026, HANDOFF D22):

1. For each district and IMD day (08:30 IST to 08:30 IST), collect the bulletin's categories. A
   warning for a subdivision or region applies to all its districts; a warning naming a district
   overrides it.
2. IMD's spatial-distribution terms set how much of the district receives each category (IMD RSMC
   terminology): isolated < 25% of the area, scattered ("a few places") 26-50%, fairly
   widespread ("many places") 51-75%, widespread ("most places") 76-100%. The fraction used is
   the middle of each range. A district is split into patches (H3 resolution 6, about 36 km^2)
   and, per member and day, a deterministic seeded draw decides which patches get which category.
   Categories nest: a higher category's patches are a subset of a lower one's. Patches outside
   every category get no warned rain (0 mm, PRIOR).
3. In a wet patch, member m's daily total = lower + q_m (upper - lower), where q_m in [0, 1]
   ranks members by closest approach to the district centroid (closest = 1; IMD member 0 = 0.5).
4. Each daily total is spread evenly over its 24 hours; R(t) is the total since "now".
5. A location floods when HAND < h*(R) = clamp(k (R - R0), 0, h_max); depth = h* - HAND.
   A road closes when water over its surface exceeds 0.3 m. Roads are raised above the ground
   around them by a formation allowance per road class (PRIOR), so the road closes when
   R(t) >= R0 + (HAND + allowance + 0.3) / k, and HAND + allowance + 0.3 < h_max.

Riverine inflow from upstream districts is not modelled in the slice.
"""

import hashlib
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
# Share of the area receiving the stated category: middle of IMD's ranges (PRIOR).
COVERAGE_FRACTION: dict[str, float] = {
    "isolated": 0.125,
    "a_few": 0.38,
    "many": 0.63,
    "most": 0.88,
    "unspecified": 1.0,
}
K_M_PER_MM = 0.02  # PRIOR
R0_MM = 50.0  # PRIOR
H_MAX_M = 5.0  # PRIOR
CLOSE_DEPTH_M = 0.3  # Pregnolato et al. (2017); PRIOR for flowing water
PATCH_H3_RES = 6  # about 36 km^2 (PRIOR)

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
    # A range is written with "to", a hyphen or an en dash.
    is_range = re.search(r"\bto\b|-", text) is not None or "\u2013" in text
    days = list(range(nums[0], nums[1] + 1)) if is_range and len(nums) >= 2 else nums
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
    """Warned categories per district and IMD day, with coverage fractions and review flags."""

    table: pd.DataFrame  # district, day, category, coverage_frac, lo_mm, hi_mm
    needs_review: bool = False
    phrases_used: list[str] = field(default_factory=list)


def daily_rain(
    warnings: list[dict[str, str]], districts: pd.DataFrame, state_name: str, year: int, month: int
) -> DailyRain:
    """Applies rule steps 1-2 to a bulletin's rainfall warnings for one state."""
    cover: dict[tuple[str, date, str], float] = {}
    needs_review = False
    used = []
    other_states = {"telangana", "odisha", "tamil nadu", "west bengal", "karnataka", "kerala"}
    for w in warnings:
        cat = w["category"]
        frac = COVERAGE_FRACTION.get(w.get("coverage", "unspecified"), 1.0)
        if cat not in CATEGORY_MM:
            needs_review = True
            continue
        covered = match_districts(w["area_text"], districts, state_name)
        if covered is None:
            if not any(o in _norm(w["area_text"]) for o in other_states):
                needs_review = True
            continue
        used.append(f"{w['area_text']} | {w['date_text']} | {cat} | {w.get('coverage')}")
        for day in parse_days(w["date_text"], year, month):
            for d in covered:
                key = (d, day, cat)
                cover[key] = max(cover.get(key, 0.0), frac)
    rows = [
        {"district": d, "day": day, "category": c, "coverage_frac": f,
         "lo_mm": CATEGORY_MM[c][0], "hi_mm": CATEGORY_MM[c][1]}
        for (d, day, c), f in sorted(cover.items())
    ]  # fmt: skip
    cols = ["district", "day", "category", "coverage_frac", "lo_mm", "hi_mm"]
    return DailyRain(pd.DataFrame(rows, columns=cols), needs_review, used)


def closest_approach_rank(dist_km: NDArray[np.float64]) -> NDArray[np.float64]:
    """q in [0, 1] per member: 1 for the closest approach, 0 for the farthest (ties averaged)."""
    n = len(dist_km)
    if n == 1:
        return np.array([0.5])
    ranks = pd.Series(dist_km).rank(method="average").to_numpy() - 1  # 0 = closest
    return np.asarray(1.0 - ranks / (n - 1))


def stable_seed(*parts: object) -> int:
    """A deterministic 64-bit seed from arbitrary parts (independent of Python's hash salt)."""
    digest = hashlib.sha256("|".join(str(p) for p in parts).encode()).digest()
    return int.from_bytes(digest[:8], "little")


def patch_daily_totals(
    district_rows: pd.DataFrame, days: list[date], n_patches: int, q: float, seed_key: str
) -> NDArray[np.float64]:
    """Daily warned rain (mm) per patch for one district and member: shape (len(days), n_patches).

    Categories nest by severity: a patch drawn inside a higher category's share gets that
    category; the shares are made cumulative so higher categories sit inside lower ones.
    """
    out = np.zeros((len(days), n_patches))
    for i, day in enumerate(days):
        rows = district_rows[district_rows["day"] == day]
        if rows.empty or n_patches == 0:
            continue
        recs = sorted(
            rows.to_dict("records"),
            key=lambda r: CATEGORY_MM[str(r["category"])][::-1],
            reverse=True,
        )
        u = np.random.default_rng(stable_seed(seed_key, day.isoformat())).random(n_patches)
        assigned = np.zeros(n_patches, dtype=bool)
        cum_frac = 0.0
        for r in recs:
            cum_frac = max(cum_frac, float(r["coverage_frac"]))
            hit = (u < cum_frac) & ~assigned
            lo, hi = float(r["lo_mm"]), float(r["hi_mm"])
            out[i, hit] = lo + q * (hi - lo)
            assigned |= hit
    return out


def cumulative_from_daily(
    totals: NDArray[np.float64], days: list[date], now_utc: datetime, n_hours: int
) -> NDArray[np.float64]:
    """R(t) at hours 0..n_hours after now, per patch: shape (n_patches, n_hours + 1).

    Each IMD day runs 08:30 IST to 08:30 IST; its total falls evenly over its 24 hours.
    """
    hour_end = [now_utc + timedelta(hours=h) for h in range(n_hours + 1)]
    weights = np.zeros((len(days), n_hours + 1))
    for i, d in enumerate(days):
        start = datetime(d.year, d.month, d.day, 8, 30, tzinfo=IST)
        end = start + timedelta(days=1)
        for h in range(1, n_hours + 1):
            if start < hour_end[h] <= end:
                weights[i, h] = 1.0 / 24.0
    return np.asarray(np.cumsum(totals.T @ weights, axis=1))


def rain_threshold_mm(
    hand_m: NDArray[np.float64], allowance_m: NDArray[np.float64] | float = 0.0
) -> NDArray[np.float64]:
    """Cumulative rain at which water stands over 0.3 m above the surface (inf if never)."""
    need = hand_m + allowance_m + CLOSE_DEPTH_M
    r = R0_MM + need / K_M_PER_MM
    return np.where(np.isfinite(hand_m) & (need < H_MAX_M), r, np.inf)


def first_hour_reaching(
    cum_mm: NDArray[np.float64], threshold_mm: NDArray[np.float64]
) -> NDArray[np.float64]:
    """First hour index at which cumulative rain reaches each threshold; inf if never."""
    idx = np.searchsorted(cum_mm, threshold_mm, side="left").astype(np.float64)
    idx[idx >= len(cum_mm)] = np.inf
    return idx
