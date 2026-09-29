"""Bulletin Reader checks (AI_AGENTS §3) on the hand-entered Montha reading; no model calls."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from aurora_agents.bulletin_reader import (
    compare_with_labels,
    read_bulletin,
    response_schema,
    run_checks,
)

ROOT = Path(__file__).resolve().parents[2]
READING = json.loads(
    (ROOT / "config/storms/montha_2025/bulletins/national_21.reading.json").read_text()
)
# The PDF itself is never committed (docs/DATA.md row 15); the text layer is approximated by the quotes.
TEXT = " ".join(q["quote"] for q in READING["source_quotes"])


def _status(checks: list[dict[str, str]]) -> dict[str, str]:
    return {c["id"]: c["status"] for c in checks}


def test_hand_reading_passes_structural_checks() -> None:
    st = _status(run_checks(READING, TEXT))
    assert st["schema"] == "pass"
    assert st["basin"] == "pass"
    assert st["leads"] == "pass"
    assert st["speed"] == "pass"
    assert st["category"] == "pass"
    assert st["quote_verbatim"] == "pass"
    assert st["ensemble"] == "na"


def test_checks_catch_errors() -> None:
    r = copy.deepcopy(READING)
    r["forecast"][3]["lat"] = r["forecast"][3]["lat"] + 5  # a 500+ km jump
    r["forecast"][4]["msw_min"], r["forecast"][4]["msw_max"] = (
        150,
        160,
    )  # far above the stated category
    r["source_quotes"].append(
        {"path": "current.lat", "quote": "a sentence the bulletin never printed"}
    )
    st = _status(run_checks(r, TEXT))
    assert st["speed"] == "fail"
    assert st["category"] == "fail"
    assert st["quote_verbatim"] == "fail"


def test_schema_failure_stops_checks() -> None:
    r = copy.deepcopy(READING)
    del r["current"]
    checks = run_checks(r, TEXT)
    assert checks[0]["status"] == "fail"
    assert len(checks) == 1


def test_label_agreement() -> None:
    same = compare_with_labels(READING, READING)
    assert same["agree"] == same["total"]
    r = copy.deepcopy(READING)
    r["current"]["lat"] = 0.0
    r["forecast"] = r["forecast"][:-1]
    diff = compare_with_labels(r, READING)
    assert diff["agree"] < diff["total"]
    assert "current.lat" in diff["differs"]


def test_response_schema_is_flat() -> None:
    assert "$ref" not in json.dumps(response_schema())


def test_rejects_non_pdf() -> None:
    class NoModel:
        def generate_json(self, **kw: Any) -> Any:
            raise AssertionError("must not be called")

    with pytest.raises(ValueError, match="PDF"):
        read_bulletin(NoModel(), b"not a pdf")  # type: ignore[arg-type]
