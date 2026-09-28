"""Edge closure times per member from surge and rain flooding (ENGINE §6).

t_close(e, m) is the earliest hour at which any of these holds:

* surge water over the road surface > 0.3 m at the edge (its lowest sampled cell);
* rain-flood water over the road surface > 0.3 m along the edge (minimum HAND along the edge);
* for a bridge, culvert or ford: either approach (the adjacent edges' 200 m nearest the crossing)
  floods that deep. The crossing's own HAND is ignored: it sits over water by definition.

The road surface sits above the surrounding ground by a formation allowance per road class
(PRIOR (unconfirmed); after Indian Roads Congress practice of raising formation level above flood
level, larger for highways than for rural roads). A 90 m DEM smooths embankments away, so without
it every road would read as lying at ground level.

Closed edges stay closed for the horizon (a confirmed field report can reopen them later).
Times are hours after the run's "now"; ``inf`` means never within the horizon.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from aurora_engine.rain import CLOSE_DEPTH_M, first_hour_reaching, rain_threshold_mm

CROSSINGS = ("bridge", "culvert", "ford")
FORMATION_ALLOWANCE_M: dict[str, float] = {  # PRIOR (unconfirmed)
    "motorway": 1.0, "motorway_link": 1.0, "trunk": 1.0, "trunk_link": 1.0,
    "primary": 1.0, "primary_link": 1.0,
    "secondary": 0.6, "secondary_link": 0.6, "tertiary": 0.6, "tertiary_link": 0.6,
}  # fmt: skip
DEFAULT_ALLOWANCE_M = 0.3  # unclassified, residential, service and other local roads


@dataclass(frozen=True)
class EdgeHazardIndex:
    """Per-edge quantities that closure rules need, precomputed once per graph build."""

    patch_idx: NDArray[np.int64]  # rain patch of the edge, -1 if none
    rain_threshold_mm: NDArray[np.float64]  # cumulative rain at which water over the road > 0.3 m
    surge_cell: NDArray[np.int64]  # candidate-cell index in the surge model, -1 if none
    surge_depth_needed_m: NDArray[np.float64]  # surge depth at which the road closes
    is_crossing: NDArray[np.bool_]
    order: NDArray[np.int64]  # edge positions sorted by patch
    bounds: NDArray[np.int64]  # start offsets into ``order`` per patch (len n_patches + 1)


def formation_allowance(road_class: pd.Series) -> NDArray[np.float64]:
    allowance = road_class.map(FORMATION_ALLOWANCE_M).fillna(DEFAULT_ALLOWANCE_M)
    return np.asarray(allowance.to_numpy(), dtype=np.float64)


def approach_hand(edges: pd.DataFrame) -> NDArray[np.float64]:
    """Effective HAND per edge for closure: whole-edge minimum, or approaches for crossings.

    For a crossing edge, each end's approach HAND is the minimum over the other edges meeting at
    that end node, taken over their 200 m nearest that node. The crossing closes when either
    approach floods, so its effective HAND is the minimum of the two approach values.
    """
    hand = edges["min_hand_m"].to_numpy(dtype=np.float64).copy()
    crossing = edges["crossing_type"].isin(CROSSINGS).to_numpy()
    inc = pd.concat(
        [
            pd.DataFrame({"node": edges["u"], "edge": edges.index, "near": edges["hand_u_end_m"]}),
            pd.DataFrame({"node": edges["v"], "edge": edges.index, "near": edges["hand_v_end_m"]}),
        ],
        ignore_index=True,
    )
    inc = inc[~crossing[inc["edge"].to_numpy()]]  # approaches are non-crossing edges
    per_node = inc.groupby("node")["near"].min()
    u_app = edges["u"].map(per_node).to_numpy(dtype=np.float64)
    v_app = edges["v"].map(per_node).to_numpy(dtype=np.float64)
    app = np.fmin(u_app, v_app)  # NaN-aware: one missing approach does not hide the other
    hand[crossing] = app[crossing]
    return hand


def build_edge_index(
    edges: pd.DataFrame,
    patch_idx: NDArray[np.int64],
    n_patches: int,
    surge_cell: NDArray[np.int64] | None = None,
) -> EdgeHazardIndex:
    """Precomputes per-edge closure inputs (needs u, v, crossing_type, road_class and HAND)."""
    allowance = formation_allowance(edges["road_class"])
    hand = approach_hand(edges)
    patch_idx = np.asarray(patch_idx, dtype=np.int64)
    order = np.argsort(patch_idx, kind="stable")
    bounds = np.searchsorted(patch_idx[order], np.arange(n_patches + 1))
    return EdgeHazardIndex(
        patch_idx=patch_idx,
        rain_threshold_mm=rain_threshold_mm(hand, allowance),
        surge_cell=np.full(len(edges), -1, dtype=np.int64) if surge_cell is None else surge_cell,
        surge_depth_needed_m=allowance + CLOSE_DEPTH_M,
        is_crossing=edges["crossing_type"].isin(CROSSINGS).to_numpy(),
        order=order,
        bounds=bounds.astype(np.int64),
    )


def rain_closure_hours(
    idx: EdgeHazardIndex, cum_mm_by_patch: NDArray[np.float64]
) -> NDArray[np.float64]:
    """Rain closure hour per edge for one member; ``cum_mm_by_patch`` is (patches, hours+1)."""
    out = np.full(len(idx.patch_idx), np.inf)
    for p in range(len(idx.bounds) - 1):
        a, b = idx.bounds[p], idx.bounds[p + 1]
        if a == b:
            continue
        sel = idx.order[a:b]
        out[sel] = first_hour_reaching(cum_mm_by_patch[p], idx.rain_threshold_mm[sel])
    return out


def surge_closure_hours(
    idx: EdgeHazardIndex, depth_m: NDArray[np.float64], onset_h_by_cell: NDArray[np.float64]
) -> NDArray[np.float64]:
    """Surge closure hour per edge: onset time where water over the road exceeds 0.3 m."""
    out = np.full(len(idx.surge_cell), np.inf)
    has = idx.surge_cell >= 0
    cells = idx.surge_cell[has]
    wet = depth_m[cells] > idx.surge_depth_needed_m[has]
    out[has] = np.where(wet, onset_h_by_cell[cells], np.inf)
    return out


def combine(*hours: NDArray[np.float64]) -> NDArray[np.float64]:
    """Earliest closure across causes."""
    return np.asarray(np.minimum.reduce(hours))
