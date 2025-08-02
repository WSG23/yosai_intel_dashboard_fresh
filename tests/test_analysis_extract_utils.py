# TODO: Fix import - analytics.core.utils.results_display not found
# from analytics.core.utils.results_display import (
    _extract_counts,
    _extract_security_metrics,
)


def test_extract_counts_iterables_and_success_fallback():
    results = {
        "total_events": 10,
        "unique_users": {"u1", "u2", "u3"},
        "unique_doors": ["d1", "d2"],
        "successful_events": 8,
        "failed_events": 2,
    }
    counts = _extract_counts(results)
    assert counts["unique_users"] == 3
    assert counts["unique_doors"] == 2
    assert abs(counts["success_rate"] - 0.8) < 1e-6


def test_extract_counts_generator_and_percentage_fallback():
    users_gen = (u for u in ["u1", "u2"])
    doors_tuple = ("d1", "d2", "d3")
    results = {
        "total_events": 5,
        "unique_users": users_gen,
        "unique_doors": doors_tuple,
        "success_percentage": 60,
    }
    counts = _extract_counts(results)
    assert counts["unique_users"] == 2
    assert counts["unique_doors"] == 3
    assert counts["success_rate"] == 0.6


def test_extract_security_metrics_success_rate_fallback():
    results = {
        "security_score": {"score": 75.5, "threat_level": "medium"},
        "failed_events": 3,
        "successful_events": 7,
    }
    metrics = _extract_security_metrics(results)
    assert metrics["failed_attempts"] == 3
    assert abs(metrics["success_rate"] - 0.7) < 1e-6
