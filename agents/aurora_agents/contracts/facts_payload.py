# Generated from schemas/facts_payload.json by `make schemas`. Do not edit.

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class Source(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    table: str
    row_id: str


class Fact(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    id: Annotated[str, Field(pattern="^[a-z0-9_]+$")]
    kind: Literal[
        "probability", "count", "time", "time_window", "place", "provenance", "text"
    ]
    value: Annotated[
        float | str | list[float | str] | None,
        Field(description="Raw value; ranges and windows are [low, high]"),
    ]
    unit: str | None
    required: bool
    text: Annotated[
        dict[str, str], Field(description="Engine-rendered string per BCP-47 locale")
    ]
    source: Source


class FactsPayload(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    run_id: str
    district_lgd: str
    audience: str
    langs: Annotated[list[str], Field(min_length=1)]
    facts: list[Fact]
