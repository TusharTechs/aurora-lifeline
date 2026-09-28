"""Facility, shelter and substation classification from OSM points of interest (ENGINE §8).

Public health tiers come from OSM ``amenity``/``healthcare`` tags plus name patterns, with a
``class_confidence`` of high (tag and name agree), medium (name only) or low (tag only). Private or
untiered hospitals become ``hospital_other``: shown for context, but not access targets. SPEC §3
defines "any hospital" as the public tiers (district hospital, SDH/area hospital, CHC, PHC), and
many OSM ``amenity=hospital`` points are small clinics, so counting them would overstate access.
Clinics and doctors' offices are not hospitals and are not targets.
Nothing is invented: a facility is only what OSM says it is, and completeness is reported against
official counts separately.
"""

import json
import re

import geopandas as gpd
import pandas as pd

# Order matters: the first matching pattern wins.
TIER_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "district_hospital",
        re.compile(
            r"\b(district\s+(head\s*quarters?\s+)?hospital"
            r"|government\s+general\s+hospital|g\.?g\.?h\.?)\b",
            re.I,
        ),
    ),
    (
        "sdh_area_hospital",
        re.compile(r"\b(area\s+hospital|sub[\s-]*divisional\s+hospital|s\.?d\.?h\.?)\b", re.I),
    ),
    ("chc", re.compile(r"\b(community\s+health\s+cent(re|er)|c\.?h\.?c\.?)\b", re.I)),
    (
        "phc",
        re.compile(
            r"\b(u?primary\s+health\s+cent(re|er)|u?p\.?h\.?c\.?|urban\s+primary\s+health)\b", re.I
        ),
    ),
    (
        "sub_centre",
        re.compile(
            r"\b(sub[\s-]*cent(re|er)|health\s+and\s+wellness\s+cent(re|er)|h\.?w\.?c\.?"
            r"|village\s+health\s+clinic|ysr\s+village\s+clinic)\b",
            re.I,
        ),
    ),
]
SHELTER_NAME = re.compile(
    r"\b(cyclone\s+shelter|m\.?p\.?c\.?s\.?|multi[\s-]*purpose\s+cyclone)\b", re.I
)
EXCLUDED_SHELTER_TYPES = {
    "public_transport",
    "picnic_shelter",
    "gazebo",
    "field_shelter",
    "lean_to",
    "sun_shelter",
}
# Access targets for "cut off from any hospital" (SPEC §3). hospital_other is deliberately excluded.
HOSPITAL_TYPES = ("district_hospital", "sdh_area_hospital", "chc", "phc")
REFERRAL_TIERS = {
    "phc": ("chc", "sdh_area_hospital", "district_hospital"),
    "chc": ("sdh_area_hospital", "district_hospital"),
    "sdh_area_hospital": ("district_hospital",),
    "district_hospital": (),
}


def _classify_health(tags: dict[str, str]) -> tuple[str | None, str]:
    name = " ".join(
        filter(None, [tags.get("name"), tags.get("name:en"), tags.get("official_name")])
    )
    tagged_health = tags.get("amenity") in {"hospital", "clinic"} or tags.get("healthcare") in {
        "hospital",
        "clinic",
        "centre",
        "health_centre",
    }
    for tier, pat in TIER_PATTERNS:
        if pat.search(name):
            return tier, "high" if tagged_health else "medium"
    if tags.get("amenity") == "hospital" or tags.get("healthcare") == "hospital":
        return "hospital_other", "low"
    return None, "none"


def _is_shelter(tags: dict[str, str]) -> bool:
    if SHELTER_NAME.search(tags.get("name", "")):
        return True
    if tags.get("emergency") in {"shelter", "assembly_point"}:
        return True
    return (
        tags.get("amenity") == "shelter" and tags.get("shelter_type") not in EXCLUDED_SHELTER_TYPES
    )


def classify_pois(pois: gpd.GeoDataFrame) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """Returns (facilities, substations). ``pois.tags`` holds a JSON object per row."""
    fac_rows, sub_rows = [], []
    for row in pois.itertuples(index=False):
        tags: dict[str, str] = json.loads(row.tags) if isinstance(row.tags, str) else dict(row.tags)
        oid = f"osm_{row.osm_type[0]}{row.osm_id}"
        if tags.get("power") == "substation":
            sub_rows.append(
                {
                    "substation_id": oid,
                    "osm_id": oid,
                    "voltage_kv": _voltage_kv(tags.get("voltage")),
                    "name": tags.get("name"),
                    "geometry": row.geometry,
                }
            )
            continue
        tier, confidence = _classify_health(tags)
        if tier is not None:
            fac_rows.append(
                {
                    "facility_id": oid,
                    "type": tier,
                    "name": tags.get("name") or tier.replace("_", " "),
                    "source": "osm",
                    "class_confidence": confidence,
                    "capacity": None,
                    "is_simulated": False,
                    "geometry": row.geometry,
                }
            )
        elif _is_shelter(tags):
            fac_rows.append(
                {
                    "facility_id": oid,
                    "type": "shelter",
                    "name": tags.get("name") or "shelter",
                    "source": "osm",
                    "class_confidence": "medium",
                    "capacity": None,
                    "is_simulated": False,
                    "geometry": row.geometry,
                }
            )
    facilities = gpd.GeoDataFrame(fac_rows, geometry="geometry", crs=pois.crs)
    substations = gpd.GeoDataFrame(sub_rows, geometry="geometry", crs=pois.crs)
    return _dedupe(facilities), substations


def _voltage_kv(v: str | None) -> float | None:
    if not v:
        return None
    try:
        return max(float(x) for x in re.split(r"[;,]", v) if x.strip()) / 1000.0
    except ValueError:
        return None


def _dedupe(fac: gpd.GeoDataFrame, radius_m: float = 150.0) -> gpd.GeoDataFrame:
    """Drops same-type duplicates within 150 m that share a normalised name (DATA §2 row 4)."""
    if fac.empty:
        return fac
    m = fac.to_crs("EPSG:32644")
    key = fac["name"].str.lower().str.replace(r"[^a-z0-9]", "", regex=True)
    rank = fac["class_confidence"].map({"high": 0, "medium": 1, "low": 2}).fillna(3)
    order = rank.sort_values(kind="stable").index
    kept: list[int] = []
    for i in order:
        p = m.geometry.loc[i]
        if any(
            fac.at[j, "type"] == fac.at[i, "type"]
            and key.loc[j] == key.loc[i]
            and m.geometry.loc[j].distance(p) < radius_m
            for j in kept
        ):
            continue
        kept.append(i)
    return fac.loc[sorted(kept)].reset_index(drop=True)


def referral_targets(facility_type: str) -> tuple[str, ...]:
    return REFERRAL_TIERS.get(facility_type, ())


def summary(fac: gpd.GeoDataFrame) -> pd.DataFrame:
    return pd.DataFrame(fac.groupby(["type", "class_confidence"]).size().unstack(fill_value=0))
