"""Threshold-based monitoring alerts for metrics, drift and errors."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from yosai_intel_dashboard.src.database.infrastructure_events import get_active_events
from yosai_intel_dashboard.src.services.notification_service import NotificationService


@dataclass
class AlertThresholds:
    """Threshold configuration for alert checks."""

    metrics: Dict[str, float] = field(default_factory=dict)
    drift: float = 0.1
    error_spike: int = 10


# ------------------------------------------------------------------


def _load_thresholds() -> AlertThresholds:
    from yosai_intel_dashboard.src.infrastructure.config import get_monitoring_config

    cfg = get_monitoring_config()
    if isinstance(cfg, dict):
        th_cfg = cfg.get("alert_thresholds", {})
    else:
        th_cfg = getattr(cfg, "alert_thresholds", {})
        if hasattr(th_cfg, "model_dump"):
            th_cfg = th_cfg.model_dump()
    return AlertThresholds(
        metrics=th_cfg.get("metrics", {}),
        drift=th_cfg.get("drift", 0.1),
        error_spike=th_cfg.get("error_spike", 10),
    )


class AlertManager:
    """Evaluate metrics and dispatch notifications when thresholds are exceeded."""

    def __init__(
        self,
        *,
        notifier: Optional[NotificationService] = None,
        thresholds: Optional[AlertThresholds] = None,
    ) -> None:
        self.notifier = notifier or NotificationService()
        self.thresholds = thresholds or _load_thresholds()

    # ------------------------------------------------------------------
    def notify(self, message: str) -> None:
        """Public wrapper around :meth:`_notify` for external callers."""
        self._notify(message)

    # ------------------------------------------------------------------
    def _notify(self, message: str) -> None:
        events = get_active_events()
        if events:
            details = "; ".join(f"{e.source}: {e.description}" for e in events)
            message = f"{message} | Infrastructure events: {details}"
        try:
            self.notifier.send(message)
        except Exception:  # pragma: no cover - defensive
            pass

    # ------------------------------------------------------------------
    def check_metrics(self, metrics: Dict[str, float]) -> bool:
        """Check metric values against configured thresholds."""
        triggered = False
        for name, value in metrics.items():
            limit = self.thresholds.metrics.get(name)
            if limit is not None and value < limit:
                self._notify(f"Metric {name} below threshold: {value} < {limit}")
                triggered = True
        return triggered

    # ------------------------------------------------------------------
    def check_drift(self, score: float) -> bool:
        """Check drift score against threshold."""
        if score > self.thresholds.drift:
            self._notify(
                f"Drift score {score} exceeds threshold {self.thresholds.drift}"
            )
            return True
        return False

    # ------------------------------------------------------------------
    def check_error_spike(self, count: int) -> bool:
        """Check error count for spikes."""
        if count > self.thresholds.error_spike:
            self._notify(
                f"Error spike detected: {count} > {self.thresholds.error_spike}"
            )
            return True
        return False


__all__ = ["AlertManager", "AlertThresholds"]
