"""API endpoints for plugin performance data."""

from __future__ import annotations

from api.adapter import api_adapter
from app import app
from flask import abort, jsonify, request

from core.cache_manager import CacheConfig, InMemoryCacheManager, cache_with_lock
from core.plugins.performance_manager import EnhancedThreadSafePluginManager
from validation.security_validator import SecurityValidator

_cache_manager = InMemoryCacheManager(CacheConfig())


class PluginPerformanceAPI:
    """Expose plugin performance metrics via REST endpoints."""

    @app.route("/v1/plugins/performance", methods=["GET"])
    @cache_with_lock(_cache_manager, ttl=10)
    def get_plugin_performance():
        manager: EnhancedThreadSafePluginManager = app._yosai_plugin_manager  # type: ignore[attr-defined]
        name = request.args.get("plugin", "")
        result = SecurityValidator().validate_input(name, "plugin")
        if not result["valid"]:
            abort(400, description="Invalid plugin")
        data = manager.get_plugin_performance_metrics(name)
        safe = api_adapter.unicode_processor.process_dict(data)
        return jsonify(safe)

    @app.route("/v1/plugins/performance/alerts", methods=["GET", "POST"])
    @cache_with_lock(_cache_manager, ttl=30)
    def manage_performance_alerts():
        manager: EnhancedThreadSafePluginManager = app._yosai_plugin_manager  # type: ignore[attr-defined]
        if request.method == "POST":
            payload = request.json or {}
            for k, v in payload.items():
                check = SecurityValidator().validate_input(str(v), k)
                if not check["valid"]:
                    abort(400, description="Invalid payload")
            manager.performance_manager.performance_thresholds.update(payload)
            return jsonify({"status": "updated"})
        history = manager.performance_manager.alert_history
        safe_history = api_adapter.unicode_processor.process_dict(history)
        return jsonify(safe_history)

    @app.route("/v1/plugins/performance/benchmark", methods=["POST"])
    def benchmark_plugin_performance():
        return jsonify(
            api_adapter.unicode_processor.process_dict({"status": "not_implemented"})
        )

    @app.route("/v1/plugins/performance/config", methods=["GET", "PUT"])
    def manage_performance_config():
        manager: EnhancedThreadSafePluginManager = app._yosai_plugin_manager  # type: ignore[attr-defined]
        if request.method == "PUT":
            payload = request.json or {}
            for k, v in payload.items():
                check = SecurityValidator().validate_input(str(v), k)
                if not check["valid"]:
                    abort(400, description="Invalid payload")
            manager.performance_manager.performance_thresholds.update(payload)
            return jsonify({"status": "updated"})
        cfg = manager.performance_manager.performance_thresholds
        safe_cfg = api_adapter.unicode_processor.process_dict(cfg)
        return jsonify(safe_cfg)
