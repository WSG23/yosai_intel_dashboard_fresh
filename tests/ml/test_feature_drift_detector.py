from types import SimpleNamespace

from intel_analysis_service.ml.drift import FeatureDriftDetector, FeatureStats


def test_feature_drift_detector_triggers_and_records_metrics():
    calls: list[tuple[str, float]] = []
    metric = SimpleNamespace(labels=lambda f: SimpleNamespace(observe=lambda v: calls.append((f, v))))
    alerts: list[dict[str, float]] = []
    counter = SimpleNamespace(labels=lambda f: SimpleNamespace(inc=lambda: alerts.append({f: 1})))

    detector = FeatureDriftDetector(z_threshold=1.0, metric=metric, alert_counter=counter, alert_func=lambda d: alerts.append(d))
    features = {"age": [50.0, 52.0]}
    stats = {"age": FeatureStats(mean=30.0, std=5.0)}
    drift = detector.detect(features, stats)

    assert drift
    assert detector.last_zscores["age"] > 1.0
    assert calls and calls[0][0] == "age"
    assert alerts and "age" in alerts[0]
