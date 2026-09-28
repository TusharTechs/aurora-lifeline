import pytest

from aurora_engine.units import ms_to_kt, wind_to_ms


def test_knots_to_ms() -> None:
    assert wind_to_ms(100, "kt") == pytest.approx(51.4444, rel=1e-5)


def test_kmph_to_ms() -> None:
    assert wind_to_ms(90, "kmph") == pytest.approx(25.0)


def test_round_trip() -> None:
    assert ms_to_kt(wind_to_ms(65, "kt")) == pytest.approx(65)


def test_unknown_unit_rejected() -> None:
    with pytest.raises(ValueError, match="Unknown wind unit"):
        wind_to_ms(10, "mph")  # type: ignore[arg-type]
