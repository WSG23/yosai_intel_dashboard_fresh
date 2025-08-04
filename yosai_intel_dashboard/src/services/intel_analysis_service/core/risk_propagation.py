"""Risk propagation utilities.

This module models how risk can spread through a trust network.  Each user
starts with a ``base_risk`` score.  Risk is propagated to connected users
according to the trust value of the connection – lower trust results in a
greater proportion of the risk being transferred.  A simple decay factor is
applied at each iteration to prevent unbounded growth.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, Tuple

try:  # NumPy is optional; fall back to pure Python if unavailable.
    import numpy as np
except Exception:  # pragma: no cover - only executed when numpy missing
    np = None

TrustLink = Tuple[str, str, float]


def propagate_risk(
    base_risks: Dict[str, float],
    trust_links: Iterable[TrustLink],
    *,
    iterations: int = 1,
    decay: float = 0.5,
) -> Dict[str, float]:
    """Propagate ``base_risks`` across ``trust_links``.

    Parameters
    ----------
    base_risks:
        Mapping of user id to initial risk score.
    trust_links:
        Iterable of ``(source, target, trust)`` tuples where ``trust`` is a
        value between ``0`` and ``1``.  A trust value of ``1`` means no risk is
        transferred whereas ``0`` transfers the entire risk (before decay).
    iterations:
        Number of propagation steps to perform.  Additional iterations allow
        risk to travel further through the network.
    decay:
        Fraction of risk that remains after each hop.
    """

    edges = list(trust_links)

    if np is not None:
        nodes = {n for n in base_risks}
        for s, d, _ in edges:
            nodes.add(s)
            nodes.add(d)
        idx = {n: i for i, n in enumerate(nodes)}

        src_idx = np.fromiter((idx[s] for s, _, _ in edges), dtype=np.int64)
        dst_idx = np.fromiter((idx[d] for _, d, _ in edges), dtype=np.int64)
        trust_arr = np.fromiter((t for _, _, t in edges), dtype=float)

        risks_arr = np.zeros(len(nodes), dtype=float)
        for name, score in base_risks.items():
            risks_arr[idx[name]] = score

        for _ in range(iterations):
            new_risk = risks_arr.copy()
            transmitted = risks_arr[src_idx] * (1.0 - trust_arr) * decay
            np.add.at(new_risk, dst_idx, transmitted)
            risks_arr = new_risk

        return {node: risks_arr[i] for node, i in idx.items() if risks_arr[i]}

    by_source: Dict[str, list[Tuple[str, float]]] = defaultdict(list)
    for src, dst, trust in edges:
        by_source[src].append((dst, trust))

    risks = dict(base_risks)
    for _ in range(iterations):
        new_risks = dict(risks)
        for src, neighbours in by_source.items():
            src_risk = risks.get(src, 0.0)
            if not src_risk:
                continue
            transmitted_base = src_risk * decay
            for dst, trust in neighbours:
                transmitted = transmitted_base * (1.0 - trust)
                new_risks[dst] = new_risks.get(dst, 0.0) + transmitted
        risks = new_risks

    return risks


__all__ = ["propagate_risk", "TrustLink"]
