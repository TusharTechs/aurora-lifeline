"""Isolation times by bottleneck (widest-path) reachability (ENGINE §7).

Edges close at time ``c_e`` (``inf`` if never). Each source ``s`` (a functioning target such as a
hospital) is available until ``a_s`` (``inf``, or when its own site floods). The isolation time of
node ``v`` is the latest time at which some path from a source to ``v`` is still fully open:

    b(v) = max over paths P from s in S to v of min(a_s, min over e in P of c_e)

``v`` is isolated at time t if ``b(v) <= t``. ``b(v) = -inf`` means no route even at t0 (reported
as "no mapped route (possible OSM gap)" and excluded from probabilities). Roads are undirected.
The algorithm is a max-heap Dijkstra variant, O(E log V), compiled with numba.
"""

from dataclasses import dataclass

import numba as nb
import numpy as np
from numpy.typing import NDArray

NEG_INF = -np.inf


@dataclass(frozen=True)
class CSR:
    """Undirected adjacency: for node i, neighbours are ``nbr[indptr[i]:indptr[i+1]]``."""

    indptr: NDArray[np.int64]
    nbr: NDArray[np.int64]
    edge: NDArray[np.int64]  # edge position (0..E-1) for each adjacency entry
    n_nodes: int


def build_csr(u: NDArray[np.int64], v: NDArray[np.int64], n_nodes: int) -> CSR:
    """Builds an undirected CSR from edge endpoint positions (0..n_nodes-1)."""
    e = np.arange(len(u), dtype=np.int64)
    src = np.concatenate([u, v]).astype(np.int64)
    dst = np.concatenate([v, u]).astype(np.int64)
    eid = np.concatenate([e, e])
    order = np.lexsort((dst, src))  # sorted and deterministic
    src, dst, eid = src[order], dst[order], eid[order]
    indptr = np.zeros(n_nodes + 1, dtype=np.int64)
    np.add.at(indptr, src + 1, 1)
    return CSR(indptr=np.cumsum(indptr), nbr=dst, edge=eid, n_nodes=n_nodes)


@nb.njit(cache=True)
def _bottleneck(  # noqa: PLR0917
    indptr: NDArray[np.int64],
    nbr: NDArray[np.int64],
    edge: NDArray[np.int64],
    close_t: NDArray[np.float64],
    sources: NDArray[np.int64],
    avail: NDArray[np.float64],
) -> tuple[NDArray[np.float64], NDArray[np.int64]]:
    n = indptr.shape[0] - 1
    b = np.full(n, -np.inf)
    pred = np.full(n, -1, dtype=np.int64)
    heap = [(0.0, np.int64(0))]  # (negated b, node); max-heap via negation
    heap.pop()
    for k in range(sources.shape[0]):
        s = sources[k]
        if avail[k] > b[s]:
            b[s] = avail[k]
            pred[s] = -1
            _heappush(heap, (-avail[k], s))
    while len(heap) > 0:
        negb, u = _heappop(heap)
        bu = -negb
        if bu < b[u]:
            continue  # stale entry
        for j in range(indptr[u], indptr[u + 1]):
            w = nbr[j]
            e = edge[j]
            cand = bu if bu < close_t[e] else close_t[e]
            if cand > b[w]:
                b[w] = cand
                pred[w] = e
                _heappush(heap, (-cand, w))
    return b, pred


@nb.njit(cache=True)
def _heappush(heap, item):  # type: ignore[no-untyped-def]
    heap.append(item)
    i = len(heap) - 1
    while i > 0:
        parent = (i - 1) >> 1
        if heap[i] < heap[parent]:
            heap[i], heap[parent] = heap[parent], heap[i]
            i = parent
        else:
            break


@nb.njit(cache=True)
def _heappop(heap):  # type: ignore[no-untyped-def]
    last = heap.pop()
    if len(heap) == 0:
        return last
    top = heap[0]
    heap[0] = last
    i = 0
    n = len(heap)
    while True:
        left = 2 * i + 1
        right = left + 1
        smallest = i
        if left < n and heap[left] < heap[smallest]:
            smallest = left
        if right < n and heap[right] < heap[smallest]:
            smallest = right
        if smallest == i:
            break
        heap[i], heap[smallest] = heap[smallest], heap[i]
        i = smallest
    return top


def isolation_times(
    csr: CSR,
    close_t: NDArray[np.float64],
    sources: NDArray[np.int64],
    avail: NDArray[np.float64] | None = None,
) -> tuple[NDArray[np.float64], NDArray[np.int64]]:
    """Returns (b, pred_edge) for every node. ``close_t`` is per edge, in hours (inf = never)."""
    sources = np.asarray(sources, dtype=np.int64)
    avail_arr = (
        np.full(len(sources), np.inf) if avail is None else np.asarray(avail, dtype=np.float64)
    )
    order = np.lexsort((sources, -avail_arr))  # deterministic seeding order
    return _bottleneck(
        csr.indptr,
        csr.nbr,
        csr.edge,
        np.asarray(close_t, dtype=np.float64),
        sources[order],
        avail_arr[order],
    )


# ---------------------------------------------------------------- aggregation across members


@dataclass(frozen=True)
class IsolationSummary:
    """Per node: probability of isolation by landfall, P10/P50/P90 times and deciles (hours)."""

    p_by_landfall: NDArray[np.float64]  # nan where the node has no route at t0 in any member
    t10: NDArray[np.float64]
    t50: NDArray[np.float64]
    t90: NDArray[np.float64]
    deciles: NDArray[np.float64]  # shape (n_nodes, 9); nan where fewer finite values
    never: NDArray[np.bool_]  # b = inf in at least 90% of weighted members
    no_route: NDArray[np.bool_]  # b = -inf (no route at t0) in the majority of members


def weighted_quantiles(
    values: NDArray[np.float64], weights: NDArray[np.float64], qs: NDArray[np.float64]
) -> NDArray[np.float64]:
    """Weighted quantiles of a 1-D sample (inverse of the weighted empirical CDF)."""
    order = np.argsort(values, kind="stable")
    v, w = values[order], weights[order]
    cw = np.cumsum(w)
    if cw[-1] <= 0:
        return np.full(len(qs), np.nan)
    cdf = cw / cw[-1]
    idx = np.searchsorted(cdf, qs, side="left")
    return v[np.clip(idx, 0, len(v) - 1)]


def summarise(
    b: NDArray[np.float64], weights: NDArray[np.float64], landfall_h: float
) -> IsolationSummary:
    """Aggregates isolation times ``b`` (members x nodes) with member ``weights`` (ENGINE §7)."""
    w = np.asarray(weights, dtype=np.float64)
    w = w / w.sum()
    n_nodes = b.shape[1]
    no_route_w = (w[:, None] * np.isneginf(b)).sum(axis=0)
    routed = ~np.isneginf(b)
    wr = w[:, None] * routed
    denom = wr.sum(axis=0)
    with np.errstate(invalid="ignore", divide="ignore"):
        p = (wr * (b <= landfall_h)).sum(axis=0) / denom
        never_w = (wr * np.isposinf(b)).sum(axis=0) / denom
    p[denom == 0] = np.nan
    qs = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9])
    dec = np.full((n_nodes, 9), np.nan)
    for j in range(n_nodes):
        col = b[:, j]
        finite = np.isfinite(col)
        if finite.any():
            dec[j] = weighted_quantiles(col[finite], w[finite], qs)
    return IsolationSummary(
        p_by_landfall=p,
        t10=dec[:, 0],
        t50=dec[:, 4],
        t90=dec[:, 8],
        deciles=dec,
        never=never_w >= 0.9,
        no_route=no_route_w > 0.5,
    )


def hourly_isolated_share(
    b: NDArray[np.float64], weights: NDArray[np.float64], hours: NDArray[np.float64]
) -> NDArray[np.float64]:
    """P(isolated by t) per node and hour: shape (len(hours), n_nodes); ignores no-route members."""
    w = np.asarray(weights, dtype=np.float64) / np.sum(weights)
    routed = ~np.isneginf(b)
    denom = (w[:, None] * routed).sum(axis=0)
    out = np.empty((len(hours), b.shape[1]))
    for i, t in enumerate(hours):
        with np.errstate(invalid="ignore", divide="ignore"):
            out[i] = (w[:, None] * (routed & (b <= t))).sum(axis=0) / denom
    return out


def bottleneck_edges(
    pred: NDArray[np.int64], b: NDArray[np.float64], eu: NDArray[np.int64], ev: NDArray[np.int64]
) -> NDArray[np.int64]:
    """Critical edge per node: the edge that sets its isolation time on its widest path (ENGINE §7).

    ``pred[w]`` is the edge through which ``w`` was last improved; its parent is the other endpoint.
    Along the path b is non-increasing, so if b(parent) > b(w) the connecting edge closed at b(w)
    and is the bottleneck; if they are equal, ``w`` inherits the parent's bottleneck. Returns -1
    where source availability (not an edge) binds, or where the node is unreachable.
    """
    return _bottleneck_edges(pred, b, eu, ev)  # type: ignore[no-any-return]


@nb.njit(cache=True)
def _bottleneck_edges(pred, b, eu, ev):  # type: ignore[no-untyped-def]
    n = b.shape[0]
    crit = np.full(n, -2, dtype=np.int64)  # -2 = not yet resolved
    stack = np.empty(n, dtype=np.int64)
    for start in range(n):
        if crit[start] != -2:
            continue
        depth = 0
        w = start
        # Walk up while the answer is unknown and b stays equal to the parent's.
        while True:
            if crit[w] != -2:
                break
            e = pred[w]
            if e < 0 or (not np.isfinite(b[w]) and b[w] < 0):
                crit[w] = -1
                break
            parent = ev[e] if eu[e] == w else eu[e]
            if b[parent] > b[w]:
                crit[w] = e
                break
            stack[depth] = w
            depth += 1
            w = parent
        resolved = crit[w]
        for k in range(depth - 1, -1, -1):
            crit[stack[k]] = resolved
    return crit
