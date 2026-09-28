# Generated from schemas/field_observation.json by `make schemas`. Do not edit.

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class FieldObservation(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    asset_id: str | None
    asset_type: Literal["road", "bridge", "culvert", "facility", "substation", "other"]
    passable: Literal["yes", "no", "unknown"]
    water_depth_band: Literal[
        "none", "lt_15cm", "15_30cm", "30_60cm", "gt_60cm", "unknown"
    ]
    damage_state: Literal["none", "minor", "moderate", "severe", "destroyed", "unknown"]
    blockage: Literal[
        "none", "debris", "tree", "collapse", "water", "vehicle", "unknown"
    ]
    location_consistency: Literal["consistent", "inconsistent", "unknown"]
    time_consistency: Literal["consistent", "inconsistent", "unknown"]
    voice_language: str | None
    voice_summary_en: str | None
    evidence_notes: Annotated[
        str, Field(description="At most 60 words.", max_length=600)
    ]
    confidence: Annotated[float, Field(ge=0.0, le=1.0)]
