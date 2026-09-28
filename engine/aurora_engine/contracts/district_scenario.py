# Generated from schemas/district_scenario.json by `make schemas`. Do not edit.

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field
from typing_extensions import TypeAliasType

MembersAdditionalProperty = TypeAliasType(
    "MembersAdditionalProperty", Annotated[int, Field(ge=0)]
)


class Provenance(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    imd_bulletin_no: str
    imd_issued_at_utc: AwareDatetime
    landfall_window_text: str | None = None
    members: Annotated[
        dict[str, MembersAdditionalProperty],
        Field(description="Member count per source, e.g. IMD, ECMWF, WNX, WNX_LARGE"),
    ]
    mode: Literal["ensemble", "deterministic"]
    data_versions: dict[str, str]
    code_sha: str
    model_ids: dict[str, str]


class TimeAxis(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    now_utc: AwareDatetime
    landfall_utc: AwareDatetime
    step_h: Annotated[int, Field(ge=1)]
    n_steps: Annotated[int, Field(ge=0)]


class PopServedBySubstationsAtRisk(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    p10: float | None
    p50: float | None
    p90: float | None
    class_: Annotated[
        Literal["likely", "possible", "unlikely"] | None, Field(alias="class")
    ]


class HourlyItem(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    t_utc: AwareDatetime
    pop_cut_p10: float | None
    pop_cut_p50: float | None
    pop_cut_p90: float | None
    pop_power_risk_p50: float | None
    facilities_at_risk: Annotated[int, Field(ge=0)]


class Completeness(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    badge: Literal["good", "partial", "poor"]
    phc_ratio: float | None
    chc_ratio: float | None
    substations_mapped: Annotated[int, Field(ge=0)]


class Tiles(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    url_template: str
    layers: list[
        Literal["edges", "settlements", "facilities", "surge", "flood", "tracks"]
    ]
    minzoom: int
    maxzoom: int


class Flags(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    needs_review: bool
    screening_surge: bool
    prior_params: list[str]


class Window(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    p10: float | None
    p50: float | None
    p90: float | None


PIsolatedBySourceAdditionalProperty = TypeAliasType(
    "PIsolatedBySourceAdditionalProperty", Annotated[float, Field(ge=0.0, le=1.0)]
)


class Power(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    p: Annotated[float | None, Field(ge=0.0, le=1.0)]
    class_: Annotated[
        Literal["likely", "possible", "unlikely"] | None, Field(alias="class")
    ]


class Facility(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    facility_id: str
    type: Literal[
        "district_hospital",
        "sdh_area_hospital",
        "chc",
        "phc",
        "sub_centre",
        "shelter",
        "delivery_point",
        "dialysis",
    ]
    name: str
    lat: float
    lon: float
    is_simulated: bool
    p_isolated_by_landfall: Annotated[float | None, Field(ge=0.0, le=1.0)]
    p_isolated_by_source: Annotated[
        dict[str, PIsolatedBySourceAdditionalProperty] | None,
        Field(description="Per-source probability (D15)"),
    ] = None
    t10: AwareDatetime | None
    t50: AwareDatetime | None
    t90: AwareDatetime | None
    iso_deciles: Annotated[
        list[AwareDatetime | None], Field(max_length=9, min_length=9)
    ]
    referral_p_isolated: Annotated[float | None, Field(ge=0.0, le=1.0)]
    power: Power
    expected_births_window: Window
    badges: list[str]


class Action(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    action_id: str
    type: Literal["stage_machine", "dg_set", "move_births", "evacuate"]
    target_id: str
    deadline_utc: AwareDatetime
    deadline_basis: Annotated[
        str, Field(description="e.g. 'P10 closure - 6 h' or 'IMD-track closure - 6 h'")
    ]
    people_protected: Annotated[float, Field(ge=0.0)]
    p_event: Annotated[float | None, Field(ge=0.0, le=1.0)]
    rank: Annotated[int, Field(ge=1)]
    evidence_ref: str


class Headline(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    pop_cut_hospital: Window
    facilities_at_risk: Window
    pop_served_by_substations_at_risk: PopServedBySubstationsAtRisk
    at: Literal["landfall"]


class DistrictScenario(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    schema_version: Literal["1"]
    run_id: str
    storm_id: str
    storm_status: Literal["replay", "live"]
    district_lgd: str
    district_name: str
    provenance: Provenance
    time_axis: TimeAxis
    headline: Headline
    hourly: list[HourlyItem]
    facilities: list[Facility]
    actions: list[Action]
    completeness: Completeness
    tiles: Tiles
    flags: Flags
