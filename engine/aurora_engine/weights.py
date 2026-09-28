"""Ensemble member weights (HANDOFF D15)."""

import numpy as np
import pandas as pd
from numpy.typing import NDArray


def member_weights(members: pd.DataFrame) -> NDArray[np.float64]:
    """Equal weight per ensemble source, split equally among its members; IMD member 0 gets 0.

    IMD's own track is the deterministic reference and is reported separately, not blended.
    Weights sum to 1 when there is at least one ensemble member.
    """
    w = np.zeros(len(members))
    ens = members["source"] != "IMD"
    sources = members.loc[ens, "source"].unique()
    for s in sources:
        sel = (members["source"] == s).to_numpy()
        w[sel] = 1.0 / len(sources) / sel.sum()
    return w
