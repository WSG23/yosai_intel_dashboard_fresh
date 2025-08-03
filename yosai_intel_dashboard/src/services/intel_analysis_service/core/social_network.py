"""Social network analysis utilities.

This module provides lightweight helpers for analysing interaction graphs
within an organisation.  The goal is not to provide a full blown graph
analysis toolkit but rather a tiny subset that is sufficient for our
investigative endpoints.  Two pieces of information are extracted:

* **Informal power structures** – computed using a very small centrality
  measure where the "power" of a user equals the weighted degree of the
  node in the interaction graph.
* **Unusual collaborations** – pairs of users that interact less than the
  expected minimum amount.  These may highlight ad‑hoc collaborations that
  bypass normal reporting lines.

The implementation intentionally avoids heavy third‑party dependencies
such as :mod:`networkx` so that it can run in constrained environments and
be easily unit tested.
"""

from __future__ import annotations

from collections import Counter
from typing import Iterable, Tuple, Dict, List

Interaction = Tuple[str, str, float]


def detect_power_structures(interactions: Iterable[Interaction]) -> Dict[str, float]:
    """Return a mapping of user to an approximate "power" score.

    The score is calculated as the sum of weights of all interactions the
    user participates in.  A higher score suggests the user is central in
    the informal communication network.
    """

    power = Counter()
    for src, dst, weight in interactions:
        power[src] += weight
        power[dst] += weight
    return dict(power)


def find_unusual_collaborations(
    interactions: Iterable[Interaction], *, min_occurrences: int = 3
) -> List[Tuple[str, str]]:
    """Identify collaborations that occur fewer than ``min_occurrences`` times.

    Parameters
    ----------
    interactions:
        Iterable of ``(source, target, weight)`` tuples.
    min_occurrences:
        Minimum number of interactions required for a collaboration to be
        considered "normal".  The default of ``3`` is intentionally small to
        favour recall over precision.
    """

    pair_counts: Counter[Tuple[str, str]] = Counter()
    for src, dst, _ in interactions:
        pair = tuple(sorted((src, dst)))
        pair_counts[pair] += 1

    return [pair for pair, count in pair_counts.items() if count < min_occurrences]


__all__ = ["detect_power_structures", "find_unusual_collaborations", "Interaction"]

