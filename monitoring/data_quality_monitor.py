from __future__ import annotations

"""Data quality metric utilities."""

from dataclasses import dataclass
from typing import Optional

from core.performance import MetricType, get_performance_monitor
from core.monitoring.user_experience_metrics import AlertConfig, AlertDispatcher
from config import get_monitoring_config


@dataclass
class DataQualityMetrics:
    """Container for basic data quality metrics."""

    missing_ratio: float
    outlier_ratio: float
    schema_violations: int


class DataQualityMonitor:
    """Emit data quality metrics and trigger alerts based on thresholds."""

    def __init__(self, thresholds: Optional["DataQualityThresholds"] = None, dispatcher: Optional[AlertDispatcher] = None) -> None:
        cfg = get_monitoring_config()
        dq_cfg = getattr(cfg, "data_quality", None)
        if isinstance(dq_cfg, dict):
            from config.base import DataQualityThresholds
            self.thresholds = DataQualityThresholds(**dq_cfg)
        elif dq_cfg is not None:
            self.thresholds = dq_cfg
        else:
            from config.base import DataQualityThresholds
            self.thresholds = thresholds or DataQualityThresholds()

        alert_cfg = getattr(cfg, "alerting", {})
        if isinstance(alert_cfg, dict):
            ac = AlertConfig(
                slack_webhook=alert_cfg.get("slack_webhook"),
                email=alert_cfg.get("email"),
                webhook_url=alert_cfg.get("webhook_url"),
            )
        else:
            ac = AlertConfig(
                slack_webhook=getattr(alert_cfg, "slack_webhook", None),
                email=getattr(alert_cfg, "email", None),
                webhook_url=getattr(alert_cfg, "webhook_url", None),
            )
        self.dispatcher = dispatcher or AlertDispatcher(ac)

    # ------------------------------------------------------------------
    def emit(self, metrics: DataQualityMetrics) -> None:
        """Record metrics and send alerts if thresholds are exceeded."""
        monitor = get_performance_monitor()
        monitor.record_metric("data_quality.missing_ratio", metrics.missing_ratio, MetricType.FILE_PROCESSING)
        monitor.record_metric("data_quality.outlier_ratio", metrics.outlier_ratio, MetricType.FILE_PROCESSING)
        monitor.record_metric(
            "data_quality.schema_violations", metrics.schema_violations, MetricType.FILE_PROCESSING
        )
        self._check_thresholds(metrics)

    # ------------------------------------------------------------------
    def _check_thresholds(self, metrics: DataQualityMetrics) -> None:
        problems = []
        if metrics.missing_ratio > self.thresholds.max_missing_ratio:
            problems.append(
                f"missing {metrics.missing_ratio:.2%} > {self.thresholds.max_missing_ratio:.2%}"
            )
        if metrics.outlier_ratio > self.thresholds.max_outlier_ratio:
            problems.append(
                f"outliers {metrics.outlier_ratio:.2%} > {self.thresholds.max_outlier_ratio:.2%}"
            )
        if metrics.schema_violations > self.thresholds.max_schema_violations:
            problems.append(
                f"schema violations {metrics.schema_violations} > {self.thresholds.max_schema_violations}"
            )
        if problems:
            msg = "Data quality alert: " + "; ".join(problems)
            self.dispatcher.send_alert(msg)


_data_quality_monitor: Optional[DataQualityMonitor] = None


def get_data_quality_monitor() -> DataQualityMonitor:
    """Return global :class:`DataQualityMonitor` instance."""
    global _data_quality_monitor
    if _data_quality_monitor is None:
        _data_quality_monitor = DataQualityMonitor()
    return _data_quality_monitor


__all__ = [
    "DataQualityMetrics",
    "DataQualityMonitor",
    "get_data_quality_monitor",
]
