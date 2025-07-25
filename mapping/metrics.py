from __future__ import annotations

"""Mapping related metric utilities."""

from typing import Any, Dict, List

from yosai_intel_dashboard.src.core.performance import get_performance_monitor


def get_mapping_accuracy_summary() -> Dict[str, Any]:
    """Return aggregated statistics for mapping confidence scores."""
    monitor = get_performance_monitor()
    values: List[float] = monitor.aggregated_metrics.get(
        "column_mapping.confidence", []
    )
    if not values:
        return {"count": 0}
    values_sorted = sorted(values)
    count = len(values_sorted)
    mean = sum(values_sorted) / count
    return {
        "count": count,
        "mean": mean,
        "min": values_sorted[0],
        "max": values_sorted[-1],
        "p95": values_sorted[int(count * 0.95)] if count > 1 else values_sorted[0],
        "p99": values_sorted[int(count * 0.99)] if count > 1 else values_sorted[0],
    }


__all__ = ["get_mapping_accuracy_summary"]
