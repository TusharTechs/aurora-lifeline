"""Contract tests: schemas, samples, generated models and the vendored CAP XSD."""

import hashlib
import json
from pathlib import Path

import pytest
import xmlschema
from jsonschema import Draft7Validator, FormatChecker

from aurora_engine.contracts import DistrictScenario, FieldObservation

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "schemas"
FIXTURES = ROOT / "tests" / "fixtures" / "contracts"


def load(path: Path) -> dict[str, object]:
    data: dict[str, object] = json.loads(path.read_text())
    return data


@pytest.mark.parametrize("schema_path", sorted(SCHEMAS.glob("*.json")), ids=lambda p: p.stem)
def test_schema_is_valid_draft07(schema_path: Path) -> None:
    Draft7Validator.check_schema(load(schema_path))


def test_sample_district_validates_against_schema_and_model() -> None:
    sample = load(FIXTURES / "district_scenario.sample.json")
    validator = Draft7Validator(
        load(SCHEMAS / "district_scenario.json"), format_checker=FormatChecker()
    )
    errors = sorted(validator.iter_errors(sample), key=lambda e: list(e.path))
    assert not errors, [f"{list(e.path)}: {e.message}" for e in errors]
    model = DistrictScenario.model_validate(sample)
    assert model.facilities[0].iso_deciles is not None
    assert len(model.facilities[0].iso_deciles) == 9


def test_district_schema_rejects_unknown_fields() -> None:
    sample = load(FIXTURES / "district_scenario.sample.json")
    sample["surprise"] = 1
    assert not Draft7Validator(load(SCHEMAS / "district_scenario.json")).is_valid(sample)


def test_district_deciles_must_have_nine_entries() -> None:
    sample = load(FIXTURES / "district_scenario.sample.json")
    facilities = sample["facilities"]
    assert isinstance(facilities, list)
    facilities[0]["iso_deciles"] = facilities[0]["iso_deciles"][:8]
    assert not Draft7Validator(load(SCHEMAS / "district_scenario.json")).is_valid(sample)


def test_field_observation_confidence_bounds() -> None:
    base = {
        "asset_id": None,
        "asset_type": "bridge",
        "passable": "unknown",
        "water_depth_band": "unknown",
        "damage_state": "unknown",
        "blockage": "unknown",
        "location_consistency": "unknown",
        "time_consistency": "unknown",
        "voice_language": None,
        "voice_summary_en": None,
        "evidence_notes": "",
        "confidence": 0.5,
    }
    FieldObservation.model_validate(base)
    with pytest.raises(ValueError):
        FieldObservation.model_validate({**base, "confidence": 1.5})


def test_cap_xsd_checksum_and_load() -> None:
    xsd = SCHEMAS / "cap" / "CAP-v1.2.xsd"
    expected = (SCHEMAS / "cap" / "SHA256SUMS").read_text().split()[0]
    assert hashlib.sha256(xsd.read_bytes()).hexdigest() == expected
    schema = xmlschema.XMLSchema(str(xsd))
    assert schema.target_namespace == "urn:oasis:names:tc:emergency:cap:1.2"
