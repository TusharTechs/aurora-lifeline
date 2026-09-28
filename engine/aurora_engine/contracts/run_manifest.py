# Generated from schemas/run_manifest.json by `make schemas`. Do not edit.

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    uri: str
    sha256: Annotated[str, Field(pattern="^[0-9a-f]{64}$")]
    source: str
    issued_at_utc: AwareDatetime | None
    available_at_utc: AwareDatetime | None = None


class Member(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    source: str
    member_no: Annotated[int, Field(ge=0)]
    weight: Annotated[float | None, Field(ge=0.0)] = None


class Parameter(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    name: str
    value: Any
    status: Literal["PRIOR", "PRIOR (unconfirmed)", "CONFIRMED", "CALIBRATED"]
    source: str


class Model(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    id: str
    prompt_version: str


class Output(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    path: str
    sha256: Annotated[str, Field(pattern="^[0-9a-f]{64}$")]
    bytes: Annotated[int, Field(ge=0)]


class RunManifest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    run_id: str
    storm_id: str
    created_at_utc: AwareDatetime
    code_sha: str
    imd_bulletin_no: str
    mode: Literal["ensemble", "deterministic"]
    run_label: Annotated[
        str | None,
        Field(
            description="e.g. 'hindsight (perfect-track)'; such runs never enter skill scores"
        ),
    ] = None
    inputs: list[Input]
    members: list[Member]
    parameters: list[Parameter]
    models: list[Model]
    seed: int
    outputs: list[Output]
