"""Behavioural clique detection.

The functions in this module operate on simple access logs consisting of
``(user, resource)`` tuples.  Users are clustered into cliques based on the
set of resources they access.  Deviations from the learned clique pattern
can highlight unusual behaviour worthy of further investigation.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Set, Tuple

try:  # pragma: no cover - optional dependency
    from integrations.weather.etl import WeatherEvent
except Exception:  # pragma: no cover - fallback when integration missing
    WeatherEvent = Any  # type: ignore

AccessRecord = Tuple[str, str]
# Access record with timestamp for correlation against weather events
TimedAccessRecord = Tuple[datetime, str, str]


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


def correlate_access_with_weather(
    access_records: Iterable[TimedAccessRecord],
    weather_events: Iterable[WeatherEvent],
    window: timedelta,
    spike_threshold: int,
) -> List[datetime]:
    """Flag weather events that coincide with access spikes.

    The function joins ``access_records`` with ``weather_events`` within the
    provided time ``window``.  For each weather event, if the number of access
    records in the surrounding window meets or exceeds ``spike_threshold`` the
    event timestamp is returned.  Callers can use this to highlight anomalous
    activity such as login spikes during storms.
    """

    times = sorted(ts for ts, _u, _r in access_records)
    flagged: List[datetime] = []
    for event in weather_events:
        start = event.timestamp - window
        end = event.timestamp + window
        count = 0
        for t in times:
            if t < start:
                continue
            if t > end:
                break
            count += 1
        if count >= spike_threshold:
            flagged.append(event.timestamp)
    return flagged


__all__ = [
    "cluster_users_by_coaccess",
    "detect_behavioral_deviations",
    "correlate_access_with_weather",
    "AccessRecord",
    "TimedAccessRecord",
]

