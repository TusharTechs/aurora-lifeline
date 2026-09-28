"""Unit conversion at ingest. The engine works in SI units internally (ENGINE §1)."""

from typing import Literal

WindUnit = Literal["kt", "kmph", "ms"]

KT_TO_MS = 1852.0 / 3600.0
KMPH_TO_MS = 1000.0 / 3600.0

_TO_MS: dict[str, float] = {"kt": KT_TO_MS, "kmph": KMPH_TO_MS, "ms": 1.0}


def wind_to_ms(value: float, unit: WindUnit) -> float:
    """Converts a wind speed in knots, km/h or m/s to m/s."""
    try:
        factor = _TO_MS[unit]
    except KeyError:
        raise ValueError(f"Unknown wind unit: {unit!r}") from None
    return value * factor


def ms_to_kt(value_ms: float) -> float:
    """Converts m/s to knots."""
    return value_ms / KT_TO_MS
