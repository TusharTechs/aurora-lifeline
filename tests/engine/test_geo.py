import numpy as np
import pytest

from aurora_engine.geo import haversine_km


def test_one_degree_of_latitude() -> None:
    assert float(haversine_km(16.0, 82.0, 17.0, 82.0)) == pytest.approx(111.19, abs=0.05)


def test_zero_distance() -> None:
    assert float(haversine_km(16.9, 82.2, 16.9, 82.2)) == 0.0


def test_broadcasts_over_members() -> None:
    d = haversine_km(16.0, 82.0, np.array([16.0, 18.0]), np.array([82.0, 82.0]))
    assert d.shape == (2,)
    assert d[0] == 0.0
    assert d[1] == pytest.approx(222.39, abs=0.1)
