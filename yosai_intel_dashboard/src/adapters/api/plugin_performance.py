"""API endpoints for plugin performance data."""

from __future__ import annotations

from app import app
from flask import jsonify, request
from flask_apispec import doc, marshal_with, use_kwargs
from marshmallow import Schema, fields

from shared.errors.types import ErrorCode
from yosai_framework.errors import CODE_TO_STATUS
from yosai_intel_dashboard.src.adapters.api.adapter import api_adapter
from yosai_intel_dashboard.src.core.cache_manager import (
    CacheConfig,
    InMemoryCacheManager,
    cache_with_lock,
)
from yosai_intel_dashboard.src.core.plugins.performance_manager import (
    EnhancedThreadSafePluginManager,
)
from yosai_intel_dashboard.src.core.security import validate_user_input
from yosai_intel_dashboard.src.error_handling import ErrorCategory, ErrorHandler
from yosai_intel_dashboard.src.infrastructure.config import get_cache_config

_cache_manager = InMemoryCacheManager(CacheConfig())
handler = ErrorHandler()


class PerformanceQuerySchema(Schema):
    plugin = fields.String(load_default="")


class PerformanceResponseSchema(Schema):
    status = fields.String()
    data = fields.Dict()


class PluginPerformanceAPI:
    """Expose plugin performance metrics via REST endpoints."""

    @app.route("/v1/plugins/performance", methods=["GET"])
    @doc(description="Plugin performance metrics", tags=["plugins"])
    @use_kwargs(PerformanceQuerySchema, location="query")
    @marshal_with(PerformanceResponseSchema)
    @cache_with_lock(_cache_manager, ttl=10)
    def get_plugin_performance():
        manager: EnhancedThreadSafePluginManager = app._yosai_plugin_manager  # type: ignore[attr-defined]
        name = request.args.get("plugin", "")
        try:
            name = validate_user_input(name, "plugin")
        except Exception:
            err = handler.handle(
                ValueError("Invalid plugin"), ErrorCategory.INVALID_INPUT
            )
            return jsonify(err.to_dict()), CODE_TO_STATUS[ErrorCode.INVALID_INPUT]
        data = manager.get_plugin_performance_metrics(name)
        safe = api_adapter.unicode_processor.process_dict(data)
        return jsonify(safe)

    @app.route("/v1/plugins/performance/alerts", methods=["GET", "POST"])
    @doc(description="Manage performance alerts", tags=["plugins"])
    @cache_with_lock(_cache_manager, ttl=30)
    def manage_performance_alerts():
        manager: EnhancedThreadSafePluginManager = app._yosai_plugin_manager  # type: ignore[attr-defined]
        if request.method == "POST":
            payload = request.json or {}
            sanitized = {}
            for k, v in payload.items():
                try:
                    sanitized[k] = validate_user_input(str(v), k)
                except Exception:
                    err = handler.handle(
                        ValueError("Invalid payload"), ErrorCategory.INVALID_INPUT
                    )
                    return (
                        jsonify(err.to_dict()),
                        CODE_TO_STATUS[ErrorCode.INVALID_INPUT],
                    )
            manager.performance_manager.performance_thresholds.update(sanitized)
            return jsonify({"status": "updated"})
        history = manager.performance_manager.alert_history
        safe_history = api_adapter.unicode_processor.process_dict(history)
        return jsonify(safe_history)

    @app.route("/v1/plugins/performance/benchmark", methods=["POST"])
    @doc(description="Benchmark plugin performance", tags=["plugins"])
    def benchmark_plugin_performance():
        return jsonify(
            api_adapter.unicode_processor.process_dict({"status": "not_implemented"})
        )

    @app.route("/v1/plugins/performance/config", methods=["GET", "PUT"])
    @doc(description="Manage performance config", tags=["plugins"])
    def manage_performance_config():
        manager: EnhancedThreadSafePluginManager = app._yosai_plugin_manager  # type: ignore[attr-defined]
        if request.method == "PUT":
            payload = request.json or {}
            sanitized = {}
            for k, v in payload.items():
                try:
                    sanitized[k] = validate_user_input(str(v), k)
                except Exception:
                    err = handler.handle(
                        ValueError("Invalid payload"), ErrorCategory.INVALID_INPUT
                    )
                    return (
                        jsonify(err.to_dict()),
                        CODE_TO_STATUS[ErrorCode.INVALID_INPUT],
                    )
            manager.performance_manager.performance_thresholds.update(sanitized)
            return jsonify({"status": "updated"})
        cfg = manager.performance_manager.performance_thresholds
        safe_cfg = api_adapter.unicode_processor.process_dict(cfg)
        return jsonify(safe_cfg)
