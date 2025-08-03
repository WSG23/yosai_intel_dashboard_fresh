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

    adjacency: Dict[str, Dict[str, float]] = defaultdict(dict)
    for src, dst, trust in trust_links:
        adjacency[src][dst] = trust

    risks = dict(base_risks)
    for _ in range(iterations):
        new_risks = dict(risks)
        for src, neighbours in adjacency.items():
            for dst, trust in neighbours.items():
                transmitted = risks.get(src, 0.0) * (1.0 - trust) * decay
                new_risks[dst] = new_risks.get(dst, 0.0) + transmitted
        risks = new_risks

    return risks


__all__ = ["propagate_risk", "TrustLink"]

