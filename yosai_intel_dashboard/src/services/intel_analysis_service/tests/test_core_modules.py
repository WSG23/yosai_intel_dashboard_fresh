"""Tests for the intel analysis core modules."""

from __future__ import annotations

import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))

from intel_analysis_service.core import (  # type: ignore
    cluster_users_by_coaccess,
    detect_behavioral_deviations,
    detect_power_structures,
    find_unusual_collaborations,
    propagate_risk,
)


def test_social_network_analysis() -> None:
    interactions = [
        ("alice", "bob", 1.0),
        ("alice", "carol", 1.0),
        ("bob", "carol", 1.0),
        ("alice", "bob", 1.0),
    ]
    power = detect_power_structures(interactions)
    assert power["alice"] == 3.0
    unusual = find_unusual_collaborations(interactions, min_occurrences=2)
    assert ("alice", "carol") in unusual or ("carol", "alice") in unusual


def test_behavioral_cliques() -> None:
    records = [
        ("u1", "r1"),
        ("u1", "r2"),
        ("u2", "r1"),
        ("u2", "r2"),
        ("u3", "r3"),
    ]
    clusters = cluster_users_by_coaccess(records)
    assert any(set(v) == {"u1", "u2"} for v in clusters.values())
    deviations = detect_behavioral_deviations(records + [("u1", "r3")], clusters)
    assert deviations["u1"] == {"r3"}


def test_risk_propagation() -> None:
    base = {"a": 1.0}
    links = [("a", "b", 0.2), ("b", "c", 0.5)]
    risks = propagate_risk(base, links, iterations=2, decay=1.0)
    assert risks["b"] > 0.0 and risks["c"] > 0.0
