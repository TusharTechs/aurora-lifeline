"""Field Verifier routing and metadata stripping (AI_AGENTS §4); no model calls."""

import io
from typing import Any

from PIL import Image

from aurora_agents.field_verifier import confidence_band, read_and_strip, route

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
