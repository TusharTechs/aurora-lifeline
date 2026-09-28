import numpy as np
import pandas as pd
import pytest

from aurora_engine.weights import member_weights


def test_sources_weighted_equally_and_imd_excluded() -> None:
    m = pd.DataFrame(
        {"source": ["IMD", "ECMWF", "ECMWF", "WNX_LARGE", "WNX_LARGE", "WNX_LARGE", "WNX_LARGE"]}
    )
    w = member_weights(m)
    assert w[0] == 0.0
    assert w[1:3].sum() == pytest.approx(0.5)
    assert w[3:].sum() == pytest.approx(0.5)
    assert np.allclose(w[3:], 0.125)


def test_deterministic_mode_has_zero_weights() -> None:
    assert member_weights(pd.DataFrame({"source": ["IMD"]})).tolist() == [0.0]
