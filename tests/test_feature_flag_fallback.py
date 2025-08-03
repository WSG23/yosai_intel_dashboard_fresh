from __future__ import annotations

import json
import logging

from yosai_intel_dashboard.src.services.feature_flags import FeatureFlagManager


def test_redis_unavailable_uses_cache_and_fallback(tmp_path, caplog):
    cache = tmp_path / "feature_flags_cache.json"
    cache.write_text(json.dumps({"use_analytics_microservice": True}))

    mgr = FeatureFlagManager(
        source=None,
        redis_url="redis://localhost:1",  # unreachable
        cache_file=cache,
    )

    with caplog.at_level(logging.WARNING):
        assert mgr.is_enabled("use_analytics_microservice") is True
        assert mgr.is_enabled("use_kafka_events") is False
    assert any("fallback mode" in r.message for r in caplog.records)


def test_dependency_failure_returns_fallback(caplog):
    mgr = FeatureFlagManager(source=None, redis_url=None)
    mgr._definitions["a"] = {
        "enabled": True,
        "fallback": False,
        "requires": ["missing"],
    }
    with caplog.at_level(logging.WARNING):
        mgr._recompute_flags()
        assert mgr.is_enabled("a") is False
    assert any("Failed to evaluate feature flag a" in r.message for r in caplog.records)
