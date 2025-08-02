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
    "RealTimeUIMonitor",
    "get_ui_monitor",
    "check_cluster_health",
    "deprecated_calls",
    "record_deprecated_call",
    "start_deprecation_metrics_server",
    "InferenceDriftJob",
    "request_duration",
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
        from .data_quality_monitor import (
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
        "ModelPerformanceMonitor",
        "ModelMetrics",
        "get_model_performance_monitor",
    }:
        from .model_performance_monitor import (
            ModelMetrics,
            ModelPerformanceMonitor,
            get_model_performance_monitor,
        )

        return locals()[name]
    if name == "ModelMonitoringService":
        from .model_monitoring_service import ModelMonitoringService

        return ModelMonitoringService
    if name in {"RealTimeUIMonitor", "get_ui_monitor"}:
        from .ui_monitor import RealTimeUIMonitor, get_ui_monitor

        return locals()[name]
    if name in {
        "deprecated_calls",
        "record_deprecated_call",
        "start_deprecation_metrics_server",
    }:
        from .prometheus.deprecation import (
            deprecated_calls,
            record_deprecated_call,
            start_deprecation_metrics_server,
        )

        return locals()[name]
    if name == "InferenceDriftJob":
        from .inference_drift_job import InferenceDriftJob

        return InferenceDriftJob
    if name == "request_duration":
        from .request_metrics import request_duration

        return request_duration
    raise AttributeError(name)
