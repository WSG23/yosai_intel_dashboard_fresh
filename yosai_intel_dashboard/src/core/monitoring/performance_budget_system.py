from __future__ import annotations

"""Performance budget checks with alert integration."""

from typing import Dict

from yosai_intel_dashboard.src.core.performance import get_performance_monitor

from .user_experience_metrics import AlertDispatcher


class PerformanceBudgetSystem:
    """Compare metrics against predefined budgets."""

    def __init__(self, budgets: Dict[str, float], dispatcher: AlertDispatcher) -> None:
        self.budgets = budgets
        self.dispatcher = dispatcher

    # ------------------------------------------------------------------
    def check_metric(self, name: str, value: float) -> None:
        """Send an alert if ``value`` exceeds the configured budget."""
        threshold = self.budgets.get(name)
        if threshold is not None and value > threshold:
            msg = f"{name} exceeded budget: {value:.2f} > {threshold:.2f}"
            self.dispatcher.send_alert(msg)

    # ------------------------------------------------------------------
    def evaluate_recent_metrics(self) -> None:
        """Check all recorded metrics in the monitor against budgets."""
        monitor = get_performance_monitor()
        for metric in monitor.metrics:
            key = metric.name.split(".")[0]
            self.check_metric(key, metric.value)
