import logging
import pandas as pd
import pytest

from yosai_intel_dashboard.src.services.monitoring.drift_monitor import DriftMonitor


def test_run_logs_baseline_error(caplog):
    """DriftMonitor._run should log baseline supplier errors without raising."""

    def failing_baseline():
        raise ValueError("Baseline data error")

    monitor = DriftMonitor(
        baseline_supplier=failing_baseline,
        live_supplier=lambda: pd.DataFrame({"pred": [0, 1]}),
    )

    with caplog.at_level(logging.ERROR):
        monitor._run()

    assert "Baseline data error" in caplog.text
