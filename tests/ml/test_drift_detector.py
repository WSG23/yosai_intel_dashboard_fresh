from yosai_intel_dashboard.src.services.monitoring.drift_detector import (
    DriftDetector,
    prediction_drift_ratio,
)


def test_drift_detector_logs_metrics_and_alerts():
    alerts: list[float] = []
    detector = DriftDetector(tolerance=0.5, alert_func=lambda d: alerts.append(d))
    drift = detector.detect([2.0, 2.0], [1.0, 1.0])
    assert drift
    assert detector.last_values == [2.0, 2.0]
    assert detector.last_thresholds == [1.0, 1.0]
    assert alerts and alerts[0] == 1.0
    if hasattr(prediction_drift_ratio, "_value"):
        assert prediction_drift_ratio._value.get() == 1.0
