import json

import geopandas as gpd
from shapely.geometry import Point

from aurora_engine.facilities import HOSPITAL_TYPES, classify_pois, referral_targets


def poi(i: int, tags: dict[str, str], x: float = 82.0, y: float = 16.9) -> dict[str, object]:
    return {"osm_type": "node", "osm_id": i, "tags": json.dumps(tags), "geometry": Point(x, y)}


POIS = gpd.GeoDataFrame(
    [
        poi(1, {"amenity": "hospital", "name": "Government General Hospital, Kakinada"}),
        poi(2, {"amenity": "hospital", "name": "Area Hospital Peddapuram"}, 82.1),
        poi(3, {"amenity": "clinic", "name": "Community Health Centre Tuni"}, 82.2),
        poi(4, {"name": "PHC Gollaprolu"}, 82.3),
        poi(5, {"amenity": "hospital", "name": "Sri Sai Nursing Home"}, 82.4),
        poi(6, {"amenity": "doctors", "name": "Dr. Clinic"}, 82.5),
        poi(
            7, {"amenity": "shelter", "shelter_type": "public_transport", "name": "Bus stop"}, 82.6
        ),
        poi(8, {"name": "Cyclone Shelter Uppada"}, 82.7),
        poi(9, {"power": "substation", "voltage": "132000;33000", "name": "Samalkot SS"}, 82.8),
        poi(
            10, {"amenity": "hospital", "name": "Area Hospital Peddapuram"}, 82.1005
        ),  # duplicate of 2
    ],
    crs=4326,
)


def test_tiers_and_confidence() -> None:
    fac, _ = classify_pois(POIS)
    got = {r.facility_id: (r.type, r.class_confidence) for r in fac.itertuples()}
    assert got["osm_n1"] == ("district_hospital", "high")
    assert got["osm_n2"] == ("sdh_area_hospital", "high")
    assert got["osm_n3"] == ("chc", "high")
    assert got["osm_n4"] == ("phc", "medium")
    assert got["osm_n5"] == ("hospital_other", "low")
    assert got["osm_n8"][0] == "shelter"


def test_clinics_bus_shelters_and_duplicates_excluded() -> None:
    fac, _ = classify_pois(POIS)
    ids = set(fac.facility_id)
    assert "osm_n6" not in ids  # doctors
    assert "osm_n7" not in ids  # bus shelter
    assert "osm_n10" not in ids  # same name, same type, within 150 m of osm_n2


def test_substation_voltage() -> None:
    _, subs = classify_pois(POIS)
    assert subs.voltage_kv.tolist() == [132.0]


def test_referral_tiers() -> None:
    assert referral_targets("phc") == ("chc", "sdh_area_hospital", "district_hospital")
    assert referral_targets("district_hospital") == ()
    assert referral_targets("hospital_other") == ()


def test_private_hospitals_are_not_access_targets() -> None:
    assert "hospital_other" not in HOSPITAL_TYPES
    assert set(HOSPITAL_TYPES) == {"district_hospital", "sdh_area_hospital", "chc", "phc"}
