"""API endpoints for plugin performance data."""

from __future__ import annotations

from flask import jsonify, request

from app import app
from core.plugins.performance_manager import EnhancedThreadSafePluginManager
from advanced_cache import cache_with_lock


class PluginPerformanceAPI:
    """Expose plugin performance metrics via REST endpoints."""

    @app.route("/api/v1/plugins/performance", methods=["GET"])
    @cache_with_lock(ttl_seconds=10)
    def get_plugin_performance():
        manager: EnhancedThreadSafePluginManager = app._yosai_plugin_manager  # type: ignore[attr-defined]
        name = request.args.get("plugin")
        data = manager.get_plugin_performance_metrics(name)
        return jsonify(data)

    @app.route("/api/v1/plugins/performance/alerts", methods=["GET", "POST"])
    @cache_with_lock(ttl_seconds=30)
    def manage_performance_alerts():
        manager: EnhancedThreadSafePluginManager = app._yosai_plugin_manager  # type: ignore[attr-defined]
        if request.method == "POST":
            payload = request.json or {}
            manager.performance_manager.performance_thresholds.update(payload)
            return jsonify({"status": "updated"})
        return jsonify(manager.performance_manager.alert_history)

    @app.route("/api/v1/plugins/performance/benchmark", methods=["POST"])
    def benchmark_plugin_performance():
        return jsonify({"status": "not_implemented"})

    @app.route("/api/v1/plugins/performance/config", methods=["GET", "PUT"])
    def manage_performance_config():
        manager: EnhancedThreadSafePluginManager = app._yosai_plugin_manager  # type: ignore[attr-defined]
        if request.method == "PUT":
            manager.performance_manager.performance_thresholds.update(
                request.json or {}
            )
            return jsonify({"status": "updated"})
        return jsonify(manager.performance_manager.performance_thresholds)
