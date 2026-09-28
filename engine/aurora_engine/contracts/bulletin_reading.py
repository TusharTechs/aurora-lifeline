# Generated from schemas/bulletin_reading.json by `make schemas`. Do not edit.

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class CurrentFix(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    lat: Annotated[float, Field(ge=-90.0, le=90.0)]
    lon: Annotated[float, Field(ge=-180.0, le=360.0)]
    msw_min: float | None
    msw_max: float | None
    gust_value: float | None
    wind_unit: Literal["kt", "kmph"]
    pressure_hpa: float | None
    movement_text: str | None


class ForecastPoint(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    lead_h: Annotated[int, Field(ge=0)]
    valid_at_utc: AwareDatetime | None
    valid_at_text: str | None
    lat: Annotated[float, Field(ge=-90.0, le=90.0)]
    lon: Annotated[float, Field(ge=-180.0, le=360.0)]
    msw_min: float | None
    msw_max: float | None
    gust_value: float | None
    wind_unit: Literal["kt", "kmph"]
    category: str


class Landfall(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    window_text: str
    start_utc: AwareDatetime | None
    end_utc: AwareDatetime | None
    location_text: str
    lat: float | None
    lon: float | None


class SurgeGuidance(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    area_text: str
    height_m_min: float | None
    height_m_max: float | None


class RainfallWarning(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    area_text: str
    date_text: str
    category: Literal[
        "heavy", "heavy_to_very_heavy", "very_heavy", "extremely_heavy", "other"
    ]


class WindWarning(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    area_text: str
    date_text: str | None
    speed_min: float | None
    speed_max: float | None
    gust: float | None
    unit: Literal["kt", "kmph"]


class SourceQuote(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    path: Annotated[str, Field(description="JSON path of the field the quote supports")]
    quote: Annotated[str, Field(max_length=200)]


class BulletinReading(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    bulletin_no: str
    issued_at_utc: AwareDatetime | None
    issued_at_text: str
    system_name: str | None
    system_stage: Literal["LPA", "WML", "D", "DD", "CS", "SCS", "VSCS", "ESCS", "SuCS"]
    current: CurrentFix
    forecast: list[ForecastPoint]
    landfall: Landfall | None
    surge: list[SurgeGuidance]
    rainfall_warnings: list[RainfallWarning]
    wind_warnings: list[WindWarning]
    source_quotes: list[SourceQuote]
    uncertain_fields: list[str]
    source_note: Annotated[
        str | None,
        Field(
            description="Provenance of the reading, e.g. 'hand-entered' before the Bulletin Reader exists."
        ),
    ] = None
