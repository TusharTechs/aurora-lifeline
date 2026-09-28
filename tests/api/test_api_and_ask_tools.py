"""API routes (no model calls) and Ask AURORA tools and number guard (fake ADK contexts)."""

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from fastapi.testclient import TestClient
from google.genai import types

from aurora_agents.ask import FALLBACK, RunData, make_tools, number_guard
from aurora_api import main

ROOT = Path(__file__).resolve().parents[2]
SCENARIO = json.loads((ROOT / "tests/fixtures/scenarios/kakinada_b21_small.json").read_text())


def test_health_and_runs_list_published_runs(monkeypatch: Any) -> None:
    monkeypatch.setattr(
        main,
        "RUNS",
        {"montha_2025_b21": {"scenarios": {"13999862": SCENARIO}, "areas": {}, "manifest": {}}},
    )
    client = TestClient(main.app)
    assert client.get("/api/v1/health").json()["runs"] == ["montha_2025_b21"]
    runs = client.get("/api/v1/runs").json()
    assert runs[0]["districts"] == [{"lgd": "13999862", "name": "Kakinada"}]
    assert (
        client.post("/api/v1/advisories", json={"run_id": "nope", "district_lgd": "1"}).status_code
        == 404
    )
    assert (
        client.post(
            "/api/v1/ask", json={"run_id": "montha_2025_b21", "question": "x" * 600}
        ).status_code
        == 422
    )


def _ctx() -> Any:
    return SimpleNamespace(state={"facts": {}})


def test_tools_record_facts_in_every_language() -> None:
    tools = {t.__name__: t for t in make_tools(RunData("montha_2025_b21", {"13999862": SCENARIO}))}
    ctx = _ctx()
    out = tools["get_district_summary"]("Kakinada", tool_context=ctx)
    ids = [r["id"] for r in out["facts"]]
    assert "d_13999862_pop_p50" in ids
    fact = ctx.state["facts"]["d_13999862_pop_p50"]
    assert fact["text"]["en-IN"] == "3.3 lakh"
    assert fact["text"]["te-IN"] == "3.3 లక్షలు"
    fac = tools["list_facilities_at_risk"]("kakinada", "any", tool_context=ctx)
    assert fac["facilities"][0]["chance"]["text"].endswith("%")
    acts = tools["list_actions"]("Kakinada", tool_context=ctx)
    assert "near" in acts["actions"][0]["where"]["text"]
    assert "error" in tools["get_district_summary"]("Atlantis", tool_context=_ctx())


def _resp(text: str) -> Any:
    return SimpleNamespace(content=types.Content(role="model", parts=[types.Part(text=text)]))


def test_number_guard_accepts_placeholders_and_replaces_digits() -> None:
    ctx = _ctx()
    ctx.state["facts"] = {"d_1_pop_p50": {}}
    assert number_guard(ctx, _resp("About {{d_1_pop_p50}} people may be cut off.")) is None
    replaced = number_guard(ctx, _resp("About 3.3 lakh people may be cut off."))
    assert replaced is not None
    assert replaced.content.parts[0].text == FALLBACK
    assert ctx.state["guard_problems"]
    assert number_guard(ctx, _resp("{{made_up}} people")) is not None
