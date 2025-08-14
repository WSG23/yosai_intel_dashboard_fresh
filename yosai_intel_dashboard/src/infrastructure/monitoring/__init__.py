"""Monitoring utilities package with lazy imports."""

from __future__ import annotations

__all__ = [
    "PerformanceMonitor",
    "DataQualityMonitor",
    "DataQualityMetrics",
    "get_data_quality_monitor",
    "avro_decoding_failures",
    "compatibility_failures",
    "record_avro_failure",
    "record_compatibility_failure",
    "ModelPerformanceMonitor",
    "ModelMonitoringService",
    "ModelMetrics",
    "get_model_performance_monitor",
    "ModelPerformanceTracker",
    "RealTimeUIMonitor",
    "get_ui_monitor",
    "check_cluster_health",
    "health_check",
    "health_check_router",
    "register_health_check",
    "setup_health_checks",
    "deprecated_calls",
    "record_deprecated_call",
    "start_deprecation_metrics_server",
    "InferenceDriftJob",
    "request_duration",
    "ABTest",
    "circuit_breaker_state",
    "start_metrics_server",
    "ModelRegistryAlerting",

]


def __getattr__(name: str):
    if name == "PerformanceMonitor":
        from yosai_intel_dashboard.src.core.performance import PerformanceMonitor

        return PerformanceMonitor
    if name in {
        "DataQualityMonitor",
        "DataQualityMetrics",
        "get_data_quality_monitor",
        "avro_decoding_failures",
        "compatibility_failures",
        "record_avro_failure",
        "record_compatibility_failure",
    }:
        from .data_quality_monitor import (  # noqa: F401
            DataQualityMetrics,
            DataQualityMonitor,
            avro_decoding_failures,
            compatibility_failures,
            get_data_quality_monitor,
            record_avro_failure,
            record_compatibility_failure,
        )

        return locals()[name]
    if name == "check_cluster_health":
        from .kafka_health import check_cluster_health

        return check_cluster_health
    if name in {
        "health_check",
        "health_check_router",
        "register_health_check",
        "setup_health_checks",
    }:
        from ..discovery.health_check import (  # noqa: F401
            health_check,
            health_check_router,
            register_health_check,
            setup_health_checks,
        )

        return locals()[name]
    if name in {
        "ModelPerformanceMonitor",
        "ModelMetrics",
        "get_model_performance_monitor",
    }:
        from .model_performance_monitor import (  # noqa: F401
            ModelMetrics,
            ModelPerformanceMonitor,
            get_model_performance_monitor,
        )

        return locals()[name]
    if name == "ModelPerformanceTracker":
        from .model_performance_tracker import ModelPerformanceTracker

        return ModelPerformanceTracker
    if name == "ModelMonitoringService":
        from .model_monitoring_service import ModelMonitoringService

        return ModelMonitoringService
    if name in {"RealTimeUIMonitor", "get_ui_monitor"}:
        from .ui_monitor import RealTimeUIMonitor, get_ui_monitor  # noqa: F401

        return locals()[name]
    if name in {
        "deprecated_calls",
        "record_deprecated_call",
        "start_deprecation_metrics_server",
    }:
        from .prometheus.deprecation import (  # noqa: F401
            deprecated_calls,
            record_deprecated_call,
            start_deprecation_metrics_server,
        )

        return locals()[name]
    if name == "InferenceDriftJob":
        from .inference_drift_job import InferenceDriftJob

        return InferenceDriftJob
    if name == "ModelRegistryAlerting":
        from .model_registry_alerting import ModelRegistryAlerting

        return ModelRegistryAlerting
    if name == "request_duration":
        from .request_metrics import request_duration

        return request_duration
    if name == "ABTest":
        from .ab_testing import ABTest

        return ABTest
    if name == "circuit_breaker_state":
        from .prometheus.breaker import circuit_breaker_state  # noqa: F401

        return circuit_breaker_state
    if name == "start_metrics_server":
        from yosai_intel_dashboard.src.services.resilience.metrics import (
            start_metrics_server,
        )

        return start_metrics_server

    raise AttributeError(name)
