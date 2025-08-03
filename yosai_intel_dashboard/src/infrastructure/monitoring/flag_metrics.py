"""Prometheus counters for feature flag performance."""

from __future__ import annotations

from prometheus_client import REGISTRY, Counter
from prometheus_client.core import CollectorRegistry

if "feature_flag_evaluations_total" not in REGISTRY._names_to_collectors:
    flag_evaluations = Counter(
        "feature_flag_evaluations_total", "Number of feature flag evaluations"
    )
    variant_hits = Counter(
        "feature_flag_variant_hits_total",
        "Number of feature flag variant hits",
        ["variant"],
    )
    cache_refreshes = Counter(
        "feature_flag_cache_refreshes_total", "Number of feature flag cache refreshes"
    )
    flag_fallbacks = Counter(
        "feature_flag_fallback_total", "Number of times default flag values were used"
    )
    missing_dependencies = Counter(
        "optional_dependency_missing_total",
        "Times an optional dependency was missing",
        ["dependency"],
    )
else:  # pragma: no cover - defensive in tests
    registry = CollectorRegistry()
    flag_evaluations = Counter(
        "feature_flag_evaluations_total",
        "Number of feature flag evaluations",
        registry=registry,
    )
    variant_hits = Counter(
        "feature_flag_variant_hits_total",
        "Number of feature flag variant hits",
        ["variant"],
        registry=registry,
    )
    cache_refreshes = Counter(
        "feature_flag_cache_refreshes_total",
        "Number of feature flag cache refreshes",
        registry=registry,
    )
    flag_fallbacks = Counter(
        "feature_flag_fallback_total",
        "Number of times default flag values were used",
        registry=registry,
    )
    missing_dependencies = Counter(
        "optional_dependency_missing_total",
        "Times an optional dependency was missing",
        ["dependency"],
        registry=registry,
    )

__all__ = [
    "flag_evaluations",
    "variant_hits",
    "cache_refreshes",
    "flag_fallbacks",
    "missing_dependencies",
]
