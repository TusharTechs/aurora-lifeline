"""AURORA Lifeline API (FastAPI on Cloud Run, asia-south1), served under /api via Hosting.

Read-only over published runs (baked into the image from the web-data branch) plus the Gemini
agents. Guards against cost abuse on a public demo: per-IP rate limits, a global daily cap on
uncached model runs (Firestore counter), input size limits, and caching so the judge replay is
deterministic. Nothing here dispatches an advisory or issues an alert: advisories come back as
drafts that need officer approval (CLAUDE.md non-negotiable 3).
"""

import hashlib
import json
import logging
import os
import time
from collections import defaultdict, deque
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from aurora_agents import advisory
from aurora_agents.ask import PROMPT_VERSION as ASK_PROMPT_VERSION
from aurora_agents.ask import RunData, ask
from aurora_agents.gemini import Gemini, default_cache

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("aurora.api")

RUNS_DIR = Path(
    os.environ.get("AURORA_RUNS_DIR", Path(__file__).resolve().parents[3] / "apps/web/public/runs")
)
SITE = os.environ.get("AURORA_SITE_URL", "https://aurora-lifeline.web.app")
DAILY_MODEL_RUNS = int(os.environ.get("AURORA_DAILY_MODEL_RUNS", "300"))
PER_IP_PER_MIN = int(os.environ.get("AURORA_PER_IP_PER_MIN", "8"))
VERSION = os.environ.get("AURORA_VERSION", "dev")

app = FastAPI(
    title="AURORA Lifeline API",
    version=VERSION,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)
# The site calls the API same-origin through Hosting; only the local dev server needs CORS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


def _load_runs() -> dict[str, dict[str, Any]]:
    runs: dict[str, dict[str, Any]] = {}
    if not RUNS_DIR.exists():
        return runs
    for d in sorted(p for p in RUNS_DIR.iterdir() if p.is_dir()):
        scen = {f.stem: json.loads(f.read_text()) for f in sorted((d / "districts").glob("*.json"))}
        if not scen:
            continue
        areas = json.loads((d / "areas.json").read_text()) if (d / "areas.json").exists() else {}
        manifest = (
            json.loads((d / "manifest.json").read_text()) if (d / "manifest.json").exists() else {}
        )
        runs[d.name] = {"scenarios": scen, "areas": areas, "manifest": manifest}
    return runs


RUNS = _load_runs()
_gem: Gemini | None = None
_hits: dict[str, deque[float]] = defaultdict(deque)


def gem() -> Gemini:
    global _gem  # noqa: PLW0603 - one lazily created client per instance
    if _gem is None:
        _gem = Gemini(cache=default_cache())
    return _gem


def _rate_limit(request: Request) -> None:
    ip = (
        (request.headers.get("x-forwarded-for") or (request.client.host if request.client else "?"))
        .split(",")[0]
        .strip()
    )
    q, now = _hits[ip], time.monotonic()
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= PER_IP_PER_MIN:
        raise HTTPException(429, "Too many requests; try again in a minute.")
    q.append(now)


def _spend_model_run() -> None:
    """Global daily cap on uncached model runs, counted in Firestore (fails open if unavailable)."""
    try:
        from google.cloud import firestore  # noqa: PLC0415 - only needed on a cache miss

        db = firestore.Client()
        ref = db.collection("usage").document(datetime.now(UTC).strftime("gemini-%Y-%m-%d"))
        ref.set({"runs": firestore.Increment(1)}, merge=True)
        runs = int((ref.get().to_dict() or {}).get("runs", 0))
    except Exception:
        log.warning("usage counter unavailable")
        return
    if runs > DAILY_MODEL_RUNS:
        raise HTTPException(
            429, "The public demo's daily AI budget is used up; cached answers still work."
        )


def _run(run_id: str) -> dict[str, Any]:
    if run_id not in RUNS:
        raise HTTPException(404, f"unknown run {run_id}")
    return RUNS[run_id]


@app.get("/api/v1/health")
def health() -> dict[str, Any]:
    return {"ok": True, "version": VERSION, "runs": sorted(RUNS)}


@app.get("/api/v1/runs")
def runs() -> list[dict[str, Any]]:
    return [
        {
            "run_id": rid,
            "districts": [
                {"lgd": k, "name": v["district_name"]} for k, v in r["scenarios"].items()
            ],
        }
        for rid, r in RUNS.items()
    ]


class AdvisoryRequest(BaseModel):
    run_id: str
    district_lgd: str
    language: Literal["en-IN", "te-IN", "hi-IN"] = "en-IN"
    audience: Literal["district_officer", "health", "public_works", "power", "field_team"] = (
        "district_officer"
    )


def _response_cache_key(kind: str, payload: dict[str, Any]) -> str:
    return (
        "resp-"
        + hashlib.sha256(
            (kind + json.dumps(payload, sort_keys=True, ensure_ascii=False)).encode()
        ).hexdigest()
    )


@app.post("/api/v1/advisories")
def draft_advisory(req: AdvisoryRequest, request: Request) -> dict[str, Any]:
    run = _run(req.run_id)
    scenario = run["scenarios"].get(req.district_lgd)
    if scenario is None:
        raise HTTPException(404, "unknown district for this run")
    key = _response_cache_key("advisory", {**req.model_dump(), "v": advisory.PROMPT_VERSION})
    g = gem()
    if (hit := g.cache.get(key)) is not None:
        return {**hit["output"], "cached": True}
    _rate_limit(request)
    _spend_model_run()
    url = f"{SITE}/storm/{scenario['storm_id']}/district/{req.district_lgd}/"
    out = advisory.write_advisory(
        g, scenario, language=req.language, audience=req.audience,
        ring_lonlat=run["areas"].get(req.district_lgd), web_url=url,
    )  # fmt: skip
    if out["status"] == "draft":
        g.cache.put(key, {"output": out})
    return {**out, "cached": False}


class AskRequest(BaseModel):
    run_id: str
    question: str = Field(min_length=3, max_length=500)
    language: Literal["en-IN", "te-IN", "hi-IN"] = "en-IN"


@app.post("/api/v1/ask")
async def ask_aurora(req: AskRequest, request: Request) -> dict[str, Any]:
    run = _run(req.run_id)
    norm = " ".join(req.question.lower().split())
    key = _response_cache_key(
        "ask", {"run": req.run_id, "q": norm, "lang": req.language, "v": ASK_PROMPT_VERSION}
    )
    g = gem()
    if (hit := g.cache.get(key)) is not None:
        return {**hit["output"], "cached": True}
    _rate_limit(request)
    _spend_model_run()
    out = await ask(RunData(req.run_id, run["scenarios"]), req.question, req.language)
    if out["status"] == "answer":
        g.cache.put(key, {"output": out})
    return {**out, "cached": False}
