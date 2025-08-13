from __future__ import annotations

"""Alerting utilities tied to the :class:`ModelRegistry`."""

from dataclasses import dataclass, field
from typing import Any, Protocol


class RegistryProtocol(Protocol):  # pragma: no cover - simple protocol
    metric_thresholds: dict[str, float]
    drift_thresholds: dict[str, float]

    def list_models(self) -> list[Any]:
        ...

    def get_drift_metrics(self, name: str) -> dict[str, float]:
        ...


def _default_alert_manager():  # pragma: no cover - simple factory
    from .alerts import AlertManager

    return AlertManager()


@dataclass
class ModelRegistryAlerting:
    """Monitor registry metrics and emit alerts on threshold breaches."""

    registry: RegistryProtocol
    alert_manager: Any = field(default_factory=_default_alert_manager)

    def check(self) -> None:
        """Evaluate active models and send notifications when needed."""
        for record in self.registry.list_models():
            if not getattr(record, "is_active", False):
                continue
            metrics = record.metrics or {}
            acc_threshold = self.registry.metric_thresholds.get("accuracy")
            accuracy = metrics.get("accuracy")
            if (
                acc_threshold is not None
                and accuracy is not None
                and accuracy < acc_threshold
            ):
                self.alert_manager.notify(
                    f"Model {record.name} accuracy below threshold: {accuracy} < {acc_threshold}"
                )
            drift_metrics = self.registry.get_drift_metrics(record.name)
            for feature, score in drift_metrics.items():
                threshold = self.registry.drift_thresholds.get(feature)
                if threshold is not None and score > threshold:
                    self.alert_manager.notify(
                        f"Model {record.name} drift for {feature} exceeds threshold: {score} > {threshold}"
                    )


__all__ = ["ModelRegistryAlerting"]
