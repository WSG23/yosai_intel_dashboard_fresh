"""Behavioural clique detection.

The functions in this module operate on simple access logs consisting of
``(user, resource)`` tuples.  Users are clustered into cliques based on the
set of resources they access.  Deviations from the learned clique pattern
can highlight unusual behaviour worthy of further investigation.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Set, Tuple

AccessRecord = Tuple[str, str]


def cluster_users_by_coaccess(records: Iterable[AccessRecord]) -> Dict[frozenset[str], Set[str]]:
    """Group users into cliques based on the set of resources they access."""

    resources_per_user: Dict[str, Set[str]] = defaultdict(set)
    for user, resource in records:
        resources_per_user[user].add(resource)

    cliques: Dict[frozenset[str], Set[str]] = defaultdict(set)
    for user, resources in resources_per_user.items():
        cliques[frozenset(resources)].add(user)

    return dict(cliques)


def detect_behavioral_deviations(
    records: Iterable[AccessRecord],
    clusters: Dict[frozenset[str], Set[str]],
) -> Dict[str, Set[str]]:
    """Return resources accessed outside a user's clique pattern."""

    pattern_map: Dict[str, Set[str]] = {}
    for resources, users in clusters.items():
        for user in users:
            pattern_map[user] = set(resources)

    deviations: Dict[str, Set[str]] = defaultdict(set)
    for user, resource in records:
        expected = pattern_map.get(user)
        if expected is not None and resource not in expected:
            deviations[user].add(resource)

    return {user: res for user, res in deviations.items()}


__all__ = ["cluster_users_by_coaccess", "detect_behavioral_deviations", "AccessRecord"]

