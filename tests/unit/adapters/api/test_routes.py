import pytest
import asyncio
import importlib
import sys
import types

from fastapi import HTTPException

pytest.importorskip("api.routes")


def test_routes_module_importable():
    module = __import__("api.routes", fromlist=[""])
    assert module is not None


def test_analytics_route_sanitizes_input(monkeypatch):
    called: dict[str, str] = {}

    cfg_mod = types.SimpleNamespace(get_cache_config=lambda: types.SimpleNamespace(ttl=1))
    monkeypatch.setitem(
        sys.modules, "yosai_intel_dashboard.src.infrastructure.config", cfg_mod
    )
    analytics_router = importlib.import_module("api.analytics_router")

    def fake_summary(fid: str, rng: str) -> dict:
        called["facility_id"] = fid
        called["range"] = rng
        return {}

    monkeypatch.setattr(
        analytics_router._cached_service,
        "get_analytics_summary_sync",
        fake_summary,
    )
    payload = "<script>alert(1)</script>"
    query = analytics_router.AnalyticsQuery(facility_id=payload, range="30d")
    asyncio.run(analytics_router.get_patterns_analysis(query, None))
    assert called["facility_id"] == "&lt;script&gt;alert(1)&lt;/script&gt;"


def test_chart_invalid_type_returns_message(monkeypatch):
    cfg_mod = types.SimpleNamespace(get_cache_config=lambda: types.SimpleNamespace(ttl=1))
    monkeypatch.setitem(
        sys.modules, "yosai_intel_dashboard.src.infrastructure.config", cfg_mod
    )
    analytics_router = importlib.import_module("api.analytics_router")
    monkeypatch.setattr(
        analytics_router._cached_service,
        "get_analytics_summary_sync",
        lambda fid, rng: {},
    )
    payload = "<script>alert(1)</script>"
    query = analytics_router.AnalyticsQuery()
    with pytest.raises(HTTPException) as exc:
        asyncio.run(analytics_router.get_chart_data(payload, query, None))
    assert exc.value.detail["message"] == "Unknown chart type"
