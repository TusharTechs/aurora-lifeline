# Generated from schemas/advisory_draft.json by `make schemas`. Do not edit.

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, RootModel


class PlaceholdersUsedItem(RootModel[str]):
    root: Annotated[str, Field(pattern="^[a-z0-9_]+$")]


class Cap(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    event: str
    urgency: Literal["Immediate", "Expected", "Future"]
    severity: Literal["Extreme", "Severe", "Moderate", "Minor"]
    certainty: Literal["Observed", "Likely", "Possible"]
    category: Literal["Met", "Infra", "Health", "Safety"]


class AdvisoryDraft(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    language: Annotated[str, Field(description="BCP-47 tag, e.g. en-IN, te-IN")]
    audience: Literal[
        "district_officer", "health", "power", "public_works", "field_team"
    ]
    headline: Annotated[str, Field(max_length=100)]
    sms_text: Annotated[str, Field(max_length=320)]
    description: str
    instruction: str
    voice_script: Annotated[
        str, Field(description="At most 90 words (checked in code).")
    ]
    placeholders_used: list[PlaceholdersUsedItem]
    cap: Cap
