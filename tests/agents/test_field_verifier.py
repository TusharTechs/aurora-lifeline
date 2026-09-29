"""Field Verifier routing and metadata stripping (AI_AGENTS §4); no model calls."""

import io
from typing import Any

from PIL import Image

from aurora_agents.field_verifier import confidence_band, read_and_strip, route, verify
from aurora_agents.gemini import CallInfo

CANDS = [
    {"asset_id": "edge_1", "type": "bridge", "description": "bridge near Uppada"},
    {"asset_id": "edge_2", "type": "road", "description": "road near Tuni"},
]


def obs(**kw: Any) -> dict[str, Any]:
    base = {
        "asset_id": "edge_2",
        "passable": "no",
        "location_consistency": "consistent",
        "confidence": 0.9,
    }
    return {**base, **kw}


def test_auto_apply_only_when_every_rule_holds() -> None:
    assert route(obs(), CANDS, None)["decision"] == "auto_apply"
    for bad in (
        obs(asset_id=None),
        obs(location_consistency="unknown"),
        obs(passable="unknown"),
        obs(confidence=0.79),
    ):
        r = route(bad, CANDS, None)
        assert r["decision"] == "officer_queue"
        assert r["reasons"]


def test_bridge_reopening_always_goes_to_the_officer() -> None:
    r = route(obs(asset_id="edge_1", passable="yes"), CANDS, "closed")
    assert r["decision"] == "officer_queue"
    assert any("reopening" in x for x in r["reasons"])


def test_confidence_is_shown_as_a_band() -> None:
    assert [confidence_band(c) for c in (0.95, 0.6, 0.2)] == ["high", "medium", "low"]


def test_metadata_is_read_then_stripped() -> None:
    img = Image.new("RGB", (32, 24), (40, 80, 120))
    exif = Image.Exif()
    exif[306] = "2025:10:28 22:10:00"  # DateTime
    buf = io.BytesIO()
    img.save(buf, format="JPEG", exif=exif)
    clean, meta = read_and_strip(buf.getvalue())
    assert meta["captured_text"] == "2025:10:28 22:10:00"
    assert not Image.open(io.BytesIO(clean)).getexif()


class FakeGemini:
    """Returns the queued observations in order and records the prompts it was sent."""

    def __init__(self, *notes: str) -> None:
        self.notes = list(notes)
        self.prompts: list[list[Any]] = []

    def generate_json(self, **kw: Any) -> tuple[dict[str, Any], CallInfo]:
        self.prompts.append(kw["parts"])
        o = {
            "asset_id": None, "asset_type": "road", "passable": "no", "water_depth_band": "15_30cm",
            "damage_state": "minor", "blockage": "water", "location_consistency": "unknown",
            "time_consistency": "unknown", "voice_language": None, "voice_summary_en": None,
            "evidence_notes": self.notes.pop(0), "confidence": 0.9,
        }  # fmt: skip
        return o, CallInfo(model="fake", cached=False, key="k")


def jpeg() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (16, 16)).save(buf, format="JPEG")
    return buf.getvalue()


def run(gem: FakeGemini) -> dict[str, Any]:
    return verify(gem, jpeg(), claimed_place="p", claimed_time="t", candidates=CANDS)  # type: ignore[arg-type]


def test_numbers_in_the_notes_get_one_retry() -> None:
    gem = FakeGemini("Water about 30 cm deep.", "Water covers the road.")
    out = run(gem)
    assert len(gem.prompts) == 2 and "number check" in str(gem.prompts[1][-1])
    assert out["observation"]["evidence_notes"] == "Water covers the road."
    assert not out["notes_withheld"]


def test_notes_are_withheld_if_numbers_remain() -> None:
    out = run(FakeGemini("Water about 30 cm deep.", "Around thirty centimetres."))
    assert out["observation"]["evidence_notes"] == ""
    assert out["notes_withheld"]
