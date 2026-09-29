"""AURORA Lifeline API (FastAPI on Cloud Run, asia-south1), served under /api via Hosting.

Read-only over published runs (baked into the image from the web-data branch) plus the Gemini
agents. Guards against cost abuse on a public demo: per-IP rate limits, a global daily cap on
uncached model runs (Firestore counter), input size limits, and caching so the judge replay is
deterministic. Nothing here dispatches an advisory or issues an alert: advisories come back as
drafts that need officer approval (CLAUDE.md non-negotiable 3).
"""

import base64
import hashlib
import html
import json
import logging
import os
import re
import time
import urllib.parse
from collections import defaultdict, deque
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Literal

import httpx
import yaml
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from aurora_agents import advisory, bulletin_reader, voice
from aurora_agents.ask import PROMPT_VERSION as ASK_PROMPT_VERSION
from aurora_agents.ask import RunData, ask
from aurora_agents.gemini import Gemini, default_cache

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("aurora.api")

CONFIG_DIR = Path(
    os.environ.get("AURORA_CONFIG_DIR", Path(__file__).resolve().parents[3] / "config")
)
RUNS_DIR = Path(
    os.environ.get("AURORA_RUNS_DIR", Path(__file__).resolve().parents[3] / "apps/web/public/runs")
)
SITE = os.environ.get("AURORA_SITE_URL", "https://aurora-lifeline.web.app")
DAILY_MODEL_RUNS = int(os.environ.get("AURORA_DAILY_MODEL_RUNS", "300"))
PER_IP_PER_MIN = int(os.environ.get("AURORA_PER_IP_PER_MIN", "8"))
VERSION = os.environ.get("AURORA_VERSION", "dev")
IST = timezone(timedelta(hours=5, minutes=30))
MODEL_DOWN = "The AI service did not answer; please try again. Cached results still work."

app = FastAPI(
    title="AURORA Lifeline API",
    version=VERSION,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)
# The site calls the API same-origin through Hosting, except bulletin reading, which calls Cloud
# Run directly because a long PDF can take longer than Hosting's 60 s proxy limit.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://aurora-lifeline.web.app",
        "https://aurora-lifeline.firebaseapp.com",
        "http://localhost:3000",
    ],
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
    try:
        out = advisory.write_advisory(
            g, scenario, language=req.language, audience=req.audience,
            ring_lonlat=run["areas"].get(req.district_lgd), web_url=url,
        )  # fmt: skip
    except Exception as e:
        log.exception("advisory failed")
        raise HTTPException(502, f"{MODEL_DOWN} ({type(e).__name__}: {str(e)[:160]})") from e
    if out["status"] == "draft":
        g.cache.put(key, {"output": out})
    return {**out, "cached": False}


@app.post("/api/v1/advisories/voice")
def advisory_voice(req: AdvisoryRequest, request: Request) -> dict[str, Any]:
    """The advisory's voice script, read aloud (Gemini-TTS). Uses the cached draft when present."""
    draft = draft_advisory(req, request)
    if draft.get("status") != "draft":
        raise HTTPException(409, "The advisory draft did not pass its checks; nothing to read.")
    text = draft["rendered"][req.language]["voice_script"]
    g = gem()
    key = _response_cache_key("voice", {**req.model_dump(), "text": text})
    if (hit := g.cache.get(key)) is not None:
        return {**hit["output"], "cached": True}
    _rate_limit(request)
    try:
        out = voice.speak(text, req.language, g.cache)
    except Exception as e:
        log.exception("voice failed")
        raise HTTPException(502, f"The voice service did not answer ({type(e).__name__}).") from e
    out["text"] = text
    g.cache.put(key, {"output": out})
    return out


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
    try:
        out = await ask(RunData(req.run_id, run["scenarios"]), req.question, req.language)
    except Exception as e:
        log.exception("ask failed")
        raise HTTPException(502, f"{MODEL_DOWN} ({type(e).__name__}: {str(e)[:160]})") from e
    if out["status"] == "answer":
        g.cache.put(key, {"output": out})
    return {**out, "cached": False}


def _known_bulletins() -> list[dict[str, Any]]:
    """Bulletins named in config/storms/*.yaml (IMD archive URL, checksum, hand-entered labels)."""
    out = []
    for f in sorted((CONFIG_DIR / "storms").glob("*.yaml")):
        cfg = yaml.safe_load(f.read_text())
        for r in cfg.get("runs", []):
            b = r.get("bulletin") or {}
            if b.get("source_url") and b.get("sha256"):
                out.append({
                    "storm_id": cfg.get("storm_id", f.stem), "bulletin_no": str(b["bulletin_no"]),
                    "product": b.get("product"), "issued_at_utc": b.get("issued_at_utc"),
                    "source_url": b["source_url"], "sha256": b["sha256"], "run_id": r["run_id"],
                    "labels_path": b.get("reading"),
                })  # fmt: skip
    return out


KNOWN = _known_bulletins()


def _labels(sha: str) -> dict[str, Any] | None:
    k = next((b for b in KNOWN if b["sha256"] == sha), None)
    if not k or not k["labels_path"]:
        return None
    path = CONFIG_DIR.parent / k["labels_path"]
    return json.loads(path.read_text()) if path.exists() else None


def _read_pdf(pdf: bytes, request: Request) -> dict[str, Any]:
    sha = hashlib.sha256(pdf).hexdigest()
    key = _response_cache_key("bulletin", {"sha": sha, "v": bulletin_reader.PROMPT_VERSION})
    g = gem()
    if (hit := g.cache.get(key)) is not None:
        return {**hit["output"], "cached": True}
    _rate_limit(request)
    _spend_model_run()
    try:
        out = bulletin_reader.read_bulletin(g, pdf, labels=_labels(sha))
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    except Exception as e:
        log.exception("bulletin read failed")
        raise HTTPException(502, f"{MODEL_DOWN} ({type(e).__name__}: {str(e)[:160]})") from e
    known = next((b for b in KNOWN if b["sha256"] == sha), None)
    out["known"] = known and {
        k: known[k] for k in ("storm_id", "bulletin_no", "run_id", "source_url")
    }
    g.cache.put(key, {"output": out})
    return {**out, "cached": False}


@app.get("/api/v1/bulletins/known")
def known_bulletins() -> list[dict[str, Any]]:
    return [
        {k: b[k] for k in ("storm_id", "bulletin_no", "issued_at_utc", "source_url", "run_id")}
        for b in KNOWN
    ]


class KnownRequest(BaseModel):
    storm_id: str
    bulletin_no: str


@app.post("/api/v1/bulletins/read-known")
def read_known(req: KnownRequest, request: Request) -> dict[str, Any]:
    """Reads a bulletin straight from IMD's archive (never re-hosted), verified by checksum."""
    b = next(
        (x for x in KNOWN if x["storm_id"] == req.storm_id and x["bulletin_no"] == req.bulletin_no),
        None,
    )
    if b is None:
        raise HTTPException(404, "unknown bulletin")
    key = _response_cache_key("bulletin", {"sha": b["sha256"], "v": bulletin_reader.PROMPT_VERSION})
    if (hit := gem().cache.get(key)) is not None:
        return {**hit["output"], "cached": True}
    try:
        pdf = (
            httpx.get(b["source_url"], timeout=30, follow_redirects=True).raise_for_status().content
        )
    except httpx.HTTPError as e:
        raise HTTPException(
            502, "Could not fetch the bulletin from IMD's archive right now."
        ) from e
    if hashlib.sha256(pdf).hexdigest() != b["sha256"]:
        raise HTTPException(502, "IMD's archive returned a different file than the one on record.")
    return _read_pdf(pdf, request)


@app.post("/api/v1/bulletins/read")
async def read_upload(request: Request, file: UploadFile = File(...)) -> dict[str, Any]:  # noqa: B008
    pdf = await file.read(bulletin_reader.MAX_PDF_BYTES + 1)
    if len(pdf) > bulletin_reader.MAX_PDF_BYTES:
        raise HTTPException(413, "PDF larger than 5 MB")
    return _read_pdf(pdf, request)


# ---------------------------------------------------------------- season watch
IMD_ARCHIVE = "https://rsmcnewdelhi.imd.gov.in/archive-information.php"
IMD_ROW = re.compile(
    r"<tr>\s*<td>\d+</td>\s*<td>(?P<title>.*?)</td>\s*<td[^>]*>(?P<listed>.*?)</td>\s*<td>(?P<file>.*?)</td>",
    re.S,
)
ACTIVE_WITHIN_H = 36
_season: dict[str, Any] = {"at": 0.0, "value": None}


def _b64(v: int | str) -> str:
    return base64.b64encode(str(v).encode()).decode()


BASED_ON = re.compile(r"based on (\d{2}):(\d{2})(?::\d{2})? UTC of (\d{2})-(\d{2})-(\d{4})", re.I)
BULLETIN_NO = re.compile(r"National_Bulletin_No[._]?0*(\d+)", re.I)


def _latest_national_bulletin() -> dict[str, Any] | None:
    """Newest IMD national bulletin: IMD issues these only while a depression or stronger exists."""
    year = datetime.now(IST).year
    params: dict[str, str | int] = {
        "internal_menu": _b64(1), "pageno": 1, "menu_id": _b64(4), "search_year": _b64(year),
    }  # fmt: skip
    text = (
        httpx.get(
            IMD_ARCHIVE, params=params, timeout=10, headers={"User-Agent": "aurora-lifeline/1.0"}
        )
        .raise_for_status()
        .text
    )
    m = IMD_ROW.search(text)
    if not m:
        return None
    title = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", m["title"]))).strip()
    href = re.search(r'href="([^"]+)"', m["file"])
    url = urllib.parse.urljoin(IMD_ARCHIVE, html.unescape(href.group(1))) if href else None
    b = BASED_ON.search(title)
    if not b:
        return None
    hh, mi, dd, mo, yy = (int(x) for x in b.groups())
    based = datetime(yy, mo, dd, hh, mi, tzinfo=UTC)
    no = BULLETIN_NO.search(url or "")
    return {
        "title": title,
        "bulletin_no": no.group(1) if no else None,
        "based_on_ist": based.astimezone(IST).strftime("%d %b %Y, %H:%M IST"),
        "age_h": round((datetime.now(UTC) - based).total_seconds() / 3600, 1),
        "url": url,
    }


@app.get("/api/v1/season")
def season() -> dict[str, Any]:
    """Is IMD issuing tropical-cyclone bulletins right now? (checked at most every 30 minutes)"""
    now = time.time()
    if _season["value"] is not None and now - _season["at"] < 1800:
        return dict(_season["value"])
    checked = datetime.now(IST).strftime("%d %b %Y, %H:%M IST")
    try:
        latest = _latest_national_bulletin()
        value: dict[str, Any] = {
            "status": "ok",
            "checked_at_ist": checked,
            "active": bool(latest and latest["age_h"] <= ACTIVE_WITHIN_H),
            "latest": latest,
            "source": "IMD RSMC New Delhi archive, national bulletins",
            "active_rule": f"a national bulletin based on observations in the last {ACTIVE_WITHIN_H} hours",
        }
    except Exception:
        log.warning("season check failed", exc_info=True)
        value = {"status": "unavailable", "checked_at_ist": checked}
    _season.update(at=now, value=value)
    return dict(value)


@app.post("/api/v1/bulletins/read-latest")
def read_latest(request: Request) -> dict[str, Any]:
    """Reads IMD's newest national bulletin (URL taken from IMD's own archive listing)."""
    info = season()
    latest = info.get("latest") or {}
    url = latest.get("url")
    if info.get("status") != "ok" or not url:
        raise HTTPException(503, "IMD's archive listing is not available right now.")
    if urllib.parse.urlparse(url).hostname != "rsmcnewdelhi.imd.gov.in":
        raise HTTPException(502, "Unexpected bulletin location.")
    try:
        pdf = httpx.get(url, timeout=30, follow_redirects=False).raise_for_status().content
    except httpx.HTTPError as e:
        raise HTTPException(
            502, "Could not fetch the bulletin from IMD's archive right now."
        ) from e
    out = _read_pdf(pdf, request)
    return {
        **out,
        "live": {
            "based_on_ist": latest.get("based_on_ist"),
            "source_url": url,
            "title": latest.get("title"),
        },
    }
