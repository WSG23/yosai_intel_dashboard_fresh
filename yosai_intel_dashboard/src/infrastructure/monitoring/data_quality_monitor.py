from __future__ import annotations

"""Data quality metric utilities."""

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Optional

pkg = sys.modules.get("monitoring")
if pkg is not None and not getattr(pkg, "__path__", None):  # fix test stubs
    pkg.__path__ = [str(Path(__file__).resolve().parent)]

try:
    from monitoring.prometheus.data_quality import (
        avro_decoding_failures,
        compatibility_failures,
    )
except Exception:  # pragma: no cover - metrics optional for tests

    class _DummyCounter:
        def inc(self) -> None:
            pass

    avro_decoding_failures = _DummyCounter()
    compatibility_failures = _DummyCounter()

if TYPE_CHECKING:  # pragma: no cover - for type hints only
    from yosai_intel_dashboard.src.infrastructure.config.base import DataQualityThresholds

else:  # pragma: no cover - runtime import for tests
    try:
        from yosai_intel_dashboard.src.infrastructure.config.base import DataQualityThresholds
    except Exception:  # pragma: no cover - minimal fallback

        class DataQualityThresholds:
            max_missing_ratio: float = 0.1
            max_outlier_ratio: float = 0.01
            max_schema_violations: int = 0
            max_avro_decode_failures: int = 0
            max_compatibility_failures: int = 0


try:  # pragma: no cover - optional dependency
    from yosai_intel_dashboard.src.infrastructure.config import get_monitoring_config
except Exception:  # pragma: no cover - minimal fallback for tests

    def get_monitoring_config() -> dict:
        return {}


# Local imports are deferred to avoid heavy dependencies during module import
if TYPE_CHECKING:  # pragma: no cover - type hints only
    from yosai_intel_dashboard.src.core.monitoring.user_experience_metrics import AlertConfig, AlertDispatcher
    from yosai_intel_dashboard.src.core.performance import MetricType


@dataclass
class DataQualityMetrics:
    """Container for basic data quality metrics."""

    missing_ratio: float
    outlier_ratio: float
    schema_violations: int


class DataQualityMonitor:
    """Emit data quality metrics and trigger alerts based on thresholds."""

    def __init__(
        self,
        thresholds: Optional["DataQualityThresholds"] = None,
        dispatcher: Optional["AlertDispatcher"] = None,
    ) -> None:
        cfg = get_monitoring_config()
        dq_cfg = getattr(cfg, "data_quality", None)
        if isinstance(dq_cfg, dict):
            from yosai_intel_dashboard.src.infrastructure.config.base import DataQualityThresholds

            self.thresholds = DataQualityThresholds(**dq_cfg)
        elif dq_cfg is not None:
            self.thresholds = dq_cfg
        else:
            from yosai_intel_dashboard.src.infrastructure.config.base import DataQualityThresholds

            self.thresholds = thresholds or DataQualityThresholds()

        alert_cfg = getattr(cfg, "alerting", {})
        if isinstance(alert_cfg, dict):
            from yosai_intel_dashboard.src.core.monitoring.user_experience_metrics import AlertConfig

            ac = AlertConfig(
                slack_webhook=alert_cfg.get("slack_webhook"),
                email=alert_cfg.get("email"),
                webhook_url=alert_cfg.get("webhook_url"),
            )
        else:
            from yosai_intel_dashboard.src.core.monitoring.user_experience_metrics import AlertConfig

            ac = AlertConfig(
                slack_webhook=getattr(alert_cfg, "slack_webhook", None),
                email=getattr(alert_cfg, "email", None),
                webhook_url=getattr(alert_cfg, "webhook_url", None),
            )
        from yosai_intel_dashboard.src.core.monitoring.user_experience_metrics import AlertDispatcher

        self.dispatcher = dispatcher or AlertDispatcher(ac)
        self._avro_failures = 0
        self._compatibility_failures = 0

    # ------------------------------------------------------------------
    def emit(self, metrics: DataQualityMetrics) -> None:
        """Record metrics and send alerts if thresholds are exceeded."""
        from yosai_intel_dashboard.src.core.performance import MetricType, get_performance_monitor

        monitor = get_performance_monitor()
        monitor.record_metric(
            "data_quality.missing_ratio",
            metrics.missing_ratio,
            MetricType.FILE_PROCESSING,
        )
        monitor.record_metric(
            "data_quality.outlier_ratio",
            metrics.outlier_ratio,
            MetricType.FILE_PROCESSING,
        )
        monitor.record_metric(
            "data_quality.schema_violations",
            metrics.schema_violations,
            MetricType.FILE_PROCESSING,
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

    # ------------------------------------------------------------------
    def record_avro_failure(self) -> None:
        """Increment counter for Avro decoding failures."""
        self._avro_failures += 1
        avro_decoding_failures.inc()
        if (
            self.thresholds.max_avro_decode_failures
            and self._avro_failures > self.thresholds.max_avro_decode_failures
        ):
            self.dispatcher.send_alert(
                "Data quality alert: avro decoding failures exceeded threshold"
            )

    # ------------------------------------------------------------------
    def record_compatibility_failure(self) -> None:
        """Increment counter for schema compatibility check failures."""
        self._compatibility_failures += 1
        compatibility_failures.inc()
        if (
            self.thresholds.max_compatibility_failures
            and self._compatibility_failures
            > self.thresholds.max_compatibility_failures
        ):
            self.dispatcher.send_alert(
                "Data quality alert: compatibility checks failed"
            )


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
    "DataQualityThresholds",
    "avro_decoding_failures",
    "compatibility_failures",
    "record_avro_failure",
    "record_compatibility_failure",
    "get_data_quality_monitor",
]
