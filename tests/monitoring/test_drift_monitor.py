import os
import os

import pandas as pd

os.environ.setdefault("LIGHTWEIGHT_SERVICES", "1")

from services.monitoring.drift_monitor import DriftMonitor


def test_alert_triggered_and_metrics_persisted():
    baseline = pd.DataFrame({"pred": [0] * 100 + [1] * 100})
    current = pd.DataFrame({"pred": [0] * 200})

    saved_metrics = []
    alerts = []

    monitor = DriftMonitor(
        baseline_supplier=lambda: baseline,
        live_supplier=lambda: current,
        thresholds={"psi": 0.1},
        metric_store=lambda m: saved_metrics.append(m),
        alert_func=lambda col, m: alerts.append((col, m)),
    )

    monitor._run()

    assert saved_metrics, "metrics should be persisted"
    assert alerts, "alert should trigger when threshold exceeded"


def test_no_alert_when_below_threshold():
    baseline = pd.DataFrame({"pred": [0] * 100 + [1] * 100})
    current = pd.DataFrame({"pred": [0] * 100 + [1] * 100})

    alerts = []

    monitor = DriftMonitor(
        baseline_supplier=lambda: baseline,
        live_supplier=lambda: current,
        thresholds={"psi": 0.1},
        alert_func=lambda col, m: alerts.append((col, m)),
    )

    monitor._run()

    assert not alerts, "no alert expected when within threshold"
