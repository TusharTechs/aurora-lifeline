"""Number safety, facts payload and CAP output (AI_AGENTS §2, §5)."""

import json
import re
from pathlib import Path
from typing import Any

import jsonschema
import pytest

from aurora_agents import cap, numbers
from aurora_agents.advisory import prompt_facts, write_advisory
from aurora_agents.facts import (
    build_facts,
    fmt_people,
    fmt_prob,
    fmt_time,
    indian_group,
    schema_view,
)
from aurora_agents.gemini import CallInfo

ROOT = Path(__file__).resolve().parents[2]
SCENARIO = json.loads((ROOT / "tests/fixtures/scenarios/kakinada_b21_small.json").read_text())


# ------------------------------------------------------------------ numbers
def test_check_rejects_ascii_and_indic_digits_and_words() -> None:
    allowed = ["pop_cut_p50"]
    assert numbers.check({"a": "About {{pop_cut_p50}} people"}, allowed).ok
    assert not numbers.check({"a": "About 3 lakh people"}, allowed).ok
    assert not numbers.check({"a": "సుమారు ౩ లక్షలు"}, allowed).ok  # Telugu digit three
    assert not numbers.check({"a": "लगभग ३ लाख"}, allowed).ok  # Devanagari digit three
    assert not numbers.check({"a": "about three lakh people"}, allowed).ok
    assert not numbers.check({"a": "a fifty percent chance"}, allowed).ok
    assert not numbers.check({"a": "chance {{pop_cut_p50}}%"}, allowed).ok
    assert numbers.check({"a": "no one should travel"}, allowed).ok  # "one" is allowed


def test_check_unknown_and_missing_ids() -> None:
    res = numbers.check({"a": "{{nope}} and {{x}}"}, ["x", "req"], required=["req"])
    assert not res.ok
    assert any("unknown fact id" in p for p in res.problems)
    assert any("missing required" in p for p in res.problems)


def test_render_only_fact_digits() -> None:
    assert numbers.render("By {{t}}", {"t": "28 Oct, 22:30 IST"}) == "By 28 Oct, 22:30 IST"
    with pytest.raises(ValueError, match="does not come from a fact"):
        numbers.render("By {{t}} or 5", {"t": "x"})


# ------------------------------------------------------------------ formatting
def test_indian_formats() -> None:
    assert indian_group(334619) == "3,34,619"
    assert indian_group(1062) == "1,062"
    assert fmt_people(334619, "en-IN") == "3.3 lakh"
    assert fmt_people(334619, "te-IN") == "3.3 లక్షలు"
    assert fmt_people(12345, "en-IN") == "12,300"
    assert fmt_people(87, "en-IN") == "90"
    assert fmt_prob(0.343) == "34%"
    assert fmt_prob(0.001) == "<1%"
    assert fmt_time("2025-10-28T17:00:00Z", "en-IN") == "28 Oct, 22:30 IST"
    assert fmt_time("2025-10-28T17:00:00Z", "hi-IN") == "28 अक्टूबर, 22:30 IST"


# ------------------------------------------------------------------ facts
def test_facts_payload_is_schema_valid_and_complete() -> None:
    payload = build_facts(SCENARIO)
    schema = json.loads((ROOT / "schemas/facts_payload.json").read_text())
    jsonschema.validate(schema_view(payload), schema)
    ids = {f["id"] for f in payload["facts"]}
    assert {"provenance", "district", "pop_cut_p50", "pop_cut_range", "fac1_name", "fac1_p"} <= ids
    assert {"act1_site", "act1_deadline"} <= ids
    for f in payload["facts"]:
        assert set(f["text"]) == {"en-IN", "te-IN", "hi-IN"}
        assert re.fullmatch(r"[a-z0-9_]+", f["id"])


def test_prompt_never_shows_numeric_values() -> None:
    rows = prompt_facts(build_facts(SCENARIO))
    shown = json.dumps(
        [{k: v for k, v in r.items() if k != "id"} for r in rows], ensure_ascii=False
    )
    assert not numbers.digits_outside_placeholders(shown)


def test_deterministic_mode_has_no_probabilities() -> None:
    s = json.loads(json.dumps(SCENARIO))
    s["provenance"]["mode"] = "deterministic"
    kinds = {f["kind"] for f in build_facts(s)["facts"]}
    assert "probability" not in kinds


# ------------------------------------------------------------------ CAP
RING = [[82.0, 16.8], [82.4, 16.8], [82.4, 17.3], [82.0, 17.3]]


def _info(lang: str = "en-IN") -> dict[str, Any]:
    return {
        "language": lang,
        "headline": "Road access risk to health facilities",
        "description": "d",
        "instruction": "i",
        "cap": {"event": "Cyclone road access risk", "urgency": "Expected", "severity": "Severe",
                "certainty": "Likely", "category": "Infra"},
    }  # fmt: skip


def test_cap_is_xsd_valid_exercise_restricted() -> None:
    xml = cap.build_alert(
        scenario=SCENARIO,
        infos=[_info(), _info("te-IN")],
        ring_lonlat=RING,
        web_url="https://aurora-lifeline.web.app/",
    )
    assert cap.validate(xml) == []
    assert "<status>Exercise</status>" in xml
    assert "<scope>Restricted</scope>" in xml
    assert "<restriction>" in xml
    sent = re.search(r"<sent>(.*)</sent>", xml)
    assert sent and sent.group(1) == "2025-10-26T09:30:00+05:30"


def test_cap_polygon_is_lat_first_and_closed() -> None:
    text = cap.polygon_text(RING)
    pts = text.split()
    assert pts[0] == "16.8,82.0"
    assert pts[0] == pts[-1]
    assert len(pts) == 5


def test_cap_validate_catches_missing_restriction_and_bad_time() -> None:
    xml = cap.build_alert(
        scenario=SCENARIO, infos=[_info()], ring_lonlat=RING, web_url="https://x.example.org/"
    )
    bad = re.sub(r"\s*<restriction>.*</restriction>", "", xml)
    assert "scope=Restricted without <restriction>" in cap.validate(bad)
    bad_time = xml.replace("+05:30</sent>", "Z</sent>")
    assert any("not YYYY-MM-DD" in p or "sent" in p for p in cap.validate(bad_time))


# ------------------------------------------------------------------ advisory with a fake Gemini
class FakeGemini:
    """Returns scripted drafts in order; records prompts."""

    def __init__(self, drafts: list[dict[str, Any]]) -> None:
        self.drafts = drafts
        self.prompts: list[Any] = []
        self.cache = None

    def generate_json(self, **kw: Any) -> tuple[dict[str, Any], CallInfo]:
        self.prompts.append(kw["parts"])
        if kw["prompt_version"].startswith("backtranslate"):
            return json.loads(kw["parts"][0]), CallInfo(model="fake", cached=False)
        return self.drafts.pop(0), CallInfo(model="fake", cached=False)

    def embed(self, texts: list[str], dims: int = 768) -> list[list[float]]:
        return [[1.0, 0.0] for _ in texts]


def _draft(
    lang: str = "en-IN", sms: str = "{{district}}: {{fac1_name}} at {{fac1_p}} risk"
) -> dict[str, Any]:
    return {
        "language": lang,
        "audience": "district_officer",
        "headline": "Road access risk in {{district}}",
        "sms_text": sms,
        "description": "Derived from {{provenance}}. {{pop_cut_p50}} people ({{pop_cut_range}}) may lose road access to hospitals. {{fac1_name}}: {{fac1_p}}, {{fac1_window}}.",
        "instruction": "Pre-position machinery at {{act1_site}} by {{act1_deadline}}.",
        "voice_script": "{{district}} advisory from {{provenance}}.",
        "placeholders_used": ["district"],
        "cap": {"event": "Cyclone road access risk", "urgency": "Expected", "severity": "Severe",
                "certainty": "Likely", "category": "Infra"},
    }  # fmt: skip


def test_advisory_renders_and_builds_valid_cap() -> None:
    gem = FakeGemini([_draft()])
    out = write_advisory(
        gem, SCENARIO, ring_lonlat=RING, web_url="https://aurora-lifeline.web.app/"
    )  # type: ignore[arg-type]
    assert out["status"] == "draft"
    assert out["approval"]["state"] == "pending_officer_approval"
    assert "3.3 lakh" in out["rendered"]["en-IN"]["description"]
    assert out["cap_problems"] == []


def test_advisory_retries_once_then_rejects_digits() -> None:
    bad = _draft(sms="{{district}}: 3 PHCs at risk")
    gem = FakeGemini([bad, _draft()])
    assert write_advisory(gem, SCENARIO)["status"] == "draft"  # type: ignore[arg-type]
    assert "rejected by the number check" in gem.prompts[1][-1]
    gem2 = FakeGemini([bad, bad])
    out = write_advisory(gem2, SCENARIO)  # type: ignore[arg-type]
    assert out["status"] == "rejected"
    assert any("digits" in p for p in out["problems"])


def test_telugu_advisory_back_translation_and_badge() -> None:
    gem = FakeGemini([_draft(), _draft("te-IN")])
    out = write_advisory(gem, SCENARIO, language="te-IN", ring_lonlat=RING)  # type: ignore[arg-type]
    assert out["status"] == "draft"
    assert "machine-translated, not reviewed" in out["badges"]
    assert "3.3 లక్షలు" in out["rendered"]["te-IN"]["description"]
    assert out["checks"]["back_translation"]["threshold_status"] == "PRIOR"
    assert out["cap_problems"] == []
