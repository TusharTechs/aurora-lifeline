"""Gemini on Agent Platform, with a content-addressed cache (AI_AGENTS §1).

* Client: ``genai.Client(enterprise=True, location="global")``; project from the environment.
* Structured output via ``response_json_schema``; ``max_output_tokens`` 16,384 (it includes
  thinking); ``thinking_level`` low or medium. Temperature, top_p and top_k are never set.
* 60 s timeout; 429 and 5xx retried up to 5 times with exponential backoff and jitter.
* Cache key: sha256(model | prompt_version | schema_version | inputs). Demo storms always hit the
  cache, so the judge replay is deterministic. Media and personal data are never logged.
"""

import hashlib
import json
import logging
import os
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from google import genai
from google.cloud import storage  # type: ignore[attr-defined]
from google.genai import errors, types

log = logging.getLogger("aurora.gemini")

MODEL_MAIN = os.environ.get("GEMINI_MODEL_MAIN", "gemini-3.7-flash")
MODEL_LITE = os.environ.get("GEMINI_MODEL_LITE", "gemini-3.5-flash-lite")
MODEL_EMBED = os.environ.get("GEMINI_MODEL_EMBED", "gemini-embedding-2")
MAX_OUTPUT_TOKENS = 16384
TIMEOUT_MS = 60_000
RETRIES = 5


class Cache(Protocol):
    def get(self, key: str) -> dict[str, Any] | None: ...
    def put(self, key: str, value: dict[str, Any]) -> None: ...


class NullCache:
    def get(self, key: str) -> dict[str, Any] | None:
        return None

    def put(self, key: str, value: dict[str, Any]) -> None:
        return None


class LocalCache:
    def __init__(self, root: Path) -> None:
        self.root = root

    def get(self, key: str) -> dict[str, Any] | None:
        p = self.root / f"{key}.json"
        return json.loads(p.read_text()) if p.exists() else None

    def put(self, key: str, value: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / f"{key}.json").write_text(json.dumps(value, ensure_ascii=False, indent=1))


class GcsCache:
    def __init__(self, bucket: str, prefix: str = "cache/gemini") -> None:
        self.bucket = storage.Client().bucket(bucket)
        self.prefix = prefix

    def get(self, key: str) -> dict[str, Any] | None:
        blob = self.bucket.blob(f"{self.prefix}/{key}.json")
        try:
            return json.loads(blob.download_as_bytes())  # type: ignore[no-any-return]
        except Exception:
            return None

    def put(self, key: str, value: dict[str, Any]) -> None:
        blob = self.bucket.blob(f"{self.prefix}/{key}.json")
        blob.upload_from_string(
            json.dumps(value, ensure_ascii=False), content_type="application/json"
        )


def default_cache() -> Cache:
    bucket = os.environ.get("GCS_BUCKET_DATA")
    if bucket:
        return GcsCache(bucket)
    local = os.environ.get("AURORA_CACHE_DIR")
    return LocalCache(Path(local)) if local else NullCache()


@dataclass
class CallInfo:
    model: str
    cached: bool
    latency_ms: int = 0
    input_tokens: int | None = None
    output_tokens: int | None = None
    thinking_tokens: int | None = None
    key: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


def cache_key(model: str, prompt_version: str, schema_version: str, inputs: list[Any]) -> str:
    h = hashlib.sha256()
    for piece in (model, prompt_version, schema_version):
        h.update(piece.encode())
        h.update(b"|")
    for x in inputs:
        h.update(
            x
            if isinstance(x, bytes)
            else json.dumps(x, sort_keys=True, ensure_ascii=False).encode()
        )
        h.update(b"|")
    return h.hexdigest()


def make_client() -> genai.Client:
    return genai.Client(
        enterprise=True,
        project=os.environ.get("GOOGLE_CLOUD_PROJECT"),
        location=os.environ.get("GOOGLE_CLOUD_LOCATION", "global"),
        http_options=types.HttpOptions(timeout=TIMEOUT_MS),
    )


def _retryable(e: Exception) -> bool:
    if isinstance(e, errors.APIError):
        return e.code == 429 or (e.code is not None and e.code >= 500)
    return isinstance(e, TimeoutError | ConnectionError)


class Gemini:
    """Structured-output calls with caching and retries."""

    def __init__(self, client: genai.Client | None = None, cache: Cache | None = None) -> None:
        self._client = client
        self.cache = cache if cache is not None else default_cache()

    @property
    def client(self) -> genai.Client:
        if self._client is None:
            self._client = make_client()
        return self._client

    def generate_json(
        self,
        *,
        model: str,
        system: str,
        parts: list[types.Part | str],
        schema: dict[str, Any],
        prompt_version: str,
        schema_version: str,
        thinking: str = "low",
        cache_inputs: list[Any] | None = None,
        use_cache: bool = True,
    ) -> tuple[dict[str, Any], CallInfo]:
        """Returns the parsed JSON object and call info. ``cache_inputs`` default to the parts."""
        inputs = cache_inputs if cache_inputs is not None else [_part_bytes(p) for p in parts]
        key = cache_key(model, prompt_version, schema_version, [system, schema, *inputs])
        if use_cache and (hit := self.cache.get(key)) is not None:
            return hit["output"], CallInfo(model=model, cached=True, key=key)
        config = types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
            response_json_schema=schema,
            max_output_tokens=MAX_OUTPUT_TOKENS,
            thinking_config=types.ThinkingConfig(
                thinking_level=types.ThinkingLevel(thinking.upper())
            ),
        )
        t0 = time.monotonic()
        resp = self._call(model, parts, config)
        info = CallInfo(
            model=model, cached=False, key=key, latency_ms=int((time.monotonic() - t0) * 1000)
        )
        usage = resp.usage_metadata
        if usage is not None:
            info.input_tokens = usage.prompt_token_count
            info.output_tokens = usage.candidates_token_count
            info.thinking_tokens = usage.thoughts_token_count
        finish = resp.candidates[0].finish_reason if resp.candidates else None
        if finish is not None and finish != types.FinishReason.STOP:
            raise ValueError(f"model stopped with {finish}")
        if not resp.text:
            raise ValueError("empty model response")
        out = json.loads(resp.text)
        log.info(
            "gemini model=%s latency_ms=%d in=%s out=%s think=%s",
            model, info.latency_ms, info.input_tokens, info.output_tokens, info.thinking_tokens,
        )  # fmt: skip
        self.cache.put(key, {"output": out, "model": model, "prompt_version": prompt_version})
        return out, info

    def embed(self, texts: list[str], dims: int = 768) -> list[list[float]]:
        """gemini-embedding-2 vectors, cached like generations."""
        key = cache_key(MODEL_EMBED, "embed-v1", str(dims), list(texts))
        if (hit := self.cache.get(key)) is not None:
            return hit["output"]  # type: ignore[no-any-return]
        for attempt in range(RETRIES + 1):
            try:
                resp = self.client.models.embed_content(
                    model=MODEL_EMBED,
                    contents=texts,  # type: ignore[arg-type]
                    config=types.EmbedContentConfig(output_dimensionality=dims),
                )
                break
            except Exception as e:
                if attempt == RETRIES or not _retryable(e):
                    raise
                time.sleep(min(2**attempt, 20) + random.random())
        vectors = [list(e.values or []) for e in resp.embeddings or []]
        self.cache.put(key, {"output": vectors, "model": MODEL_EMBED})
        return vectors

    def _call(
        self, model: str, parts: list[types.Part | str], config: types.GenerateContentConfig
    ) -> types.GenerateContentResponse:
        for attempt in range(RETRIES + 1):
            try:
                contents: list[Any] = list(parts)
                return self.client.models.generate_content(
                    model=model, contents=contents, config=config
                )
            except Exception as e:
                if attempt == RETRIES or not _retryable(e):
                    raise
                time.sleep(min(2**attempt, 20) + random.random())
        raise AssertionError("unreachable")


def _part_bytes(p: types.Part | str) -> Any:
    if isinstance(p, str):
        return p
    if p.inline_data is not None and p.inline_data.data is not None:
        return hashlib.sha256(p.inline_data.data).hexdigest()
    if p.text is not None:
        return p.text
    return p.model_dump(exclude_none=True, mode="json")
