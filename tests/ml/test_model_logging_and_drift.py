import logging

import importlib
import logging
import sys
import types

# Load real numpy if a stub is present.
np = importlib.import_module("numpy")
if not hasattr(np, "__version__"):
    sys.modules.pop("numpy", None)
    np = importlib.import_module("numpy")  # type: ignore

# Provide minimal pyarrow stub for pandas compatibility.
sys.modules.setdefault("pyarrow", types.SimpleNamespace(__version__="0.0"))
try:
    import six
    sys.modules["six.moves.winreg"] = None
except Exception:
    sys.modules.setdefault("six", types.SimpleNamespace(moves=types.SimpleNamespace(winreg=None)))

win_stub = types.ModuleType("dateutil.tz.win")
win_stub.tzwin = object
win_stub.tzwinlocal = object
sys.modules.setdefault("dateutil.tz.win", win_stub)
sys.modules.setdefault("six.moves._thread", types.SimpleNamespace(allocate_lock=lambda: object()))

# Load real pandas if stubbed.
pd = importlib.import_module("pandas")
if not hasattr(pd, "date_range"):
    sys.modules.pop("pandas", None)
    pd = importlib.import_module("pandas")  # type: ignore

# Minimal OpenTelemetry stub providing ``get_tracer`` and span context manager.
from contextlib import contextmanager


@contextmanager
def _noop_span(*a, **k):
    class _Span:
        def set_attribute(self, *aa, **kk):
            pass

    yield _Span()


otel_trace = types.SimpleNamespace(
    get_tracer=lambda *a, **k: types.SimpleNamespace(
        start_as_current_span=lambda *aa, **kk: _noop_span()
    )
)
sys.modules["opentelemetry"] = types.SimpleNamespace(trace=otel_trace)
sys.modules["opentelemetry.trace"] = otel_trace

from intel_analysis_service.ml import AnomalyDetector, RiskScorer

from yosai_intel_dashboard.src.services.monitoring.drift_monitor import DriftMonitor
from intel_analysis_service.ml import ThresholdDriftDetector


class DummyDriftDetector:
    def __init__(self):
        self.values = None
        self.thresholds = None

    def detect(self, values, thresholds):
        # store values for assertion
        self.values = list(values)
        self.thresholds = list(thresholds)
        return True


def test_anomaly_detector_logs_and_detects_drift(caplog):
    train_ts = pd.date_range('2024-01-01', periods=3, freq='D')
    train_df = pd.DataFrame({'timestamp': train_ts, 'value': 1.0})
    drift = DummyDriftDetector()
    detector = AnomalyDetector(model_version="v-test", drift_detector=drift).fit(train_df)

    test_df = pd.DataFrame({'timestamp': [pd.Timestamp('2024-01-04')], 'value': [5.0]})
    with caplog.at_level(logging.INFO):
        preds = detector.predict(test_df)
    assert 'drift_detected' in preds
    assert preds['drift_detected'].iloc[0]
    assert drift.values is not None and drift.thresholds is not None
    assert 'model=v-test' in caplog.text
    assert 'thresholds' in caplog.text


def test_risk_scorer_logs_and_detects_drift(caplog):
    train_ts = pd.date_range('2024-01-01', periods=3, freq='D')
    train_df = pd.DataFrame({'timestamp': train_ts, 'a': 0.0})
    drift = DummyDriftDetector()
    scorer = RiskScorer({'a': 1.0}, model_version="v1", drift_detector=drift).fit(train_df)

    test_df = pd.DataFrame({'timestamp': [pd.Timestamp('2024-01-04')], 'a': [2.0]})
    with caplog.at_level(logging.INFO):
        result = scorer.score(test_df)
    assert 'drift_detected' in result
    assert result['drift_detected'].iloc[0]
    assert drift.values is not None and drift.thresholds is not None
    assert 'model=v1' in caplog.text
    assert 'thresholds' in caplog.text


def test_drift_monitor_logs_and_rollback():
    baseline = pd.DataFrame({"pred": [0] * 100 + [1] * 100})
    current = pd.DataFrame({"pred": [0] * 200})

    logs: list[str] = []
    alerts: list[tuple[str, dict]] = []

    monitor = DriftMonitor(
        baseline_supplier=lambda: baseline,
        live_supplier=lambda: current,
        thresholds={"psi": 0.1},
        alert_func=lambda col, m: alerts.append((col, m)),
        monitoring_hook=lambda msg: logs.append(msg),
    )

    monitor._run()

    assert any("comparison" in m for m in logs)
    assert any("breach" in m for m in logs)
    assert alerts
    history = monitor.get_recent_history()
    assert history and history[-1]["pred"]["psi"] > 0
    assert monitor.get_recent_history(limit=1) == history[-1:]


def test_threshold_drift_detector_metrics_and_alerts():
    class DummyHist:
        def __init__(self):
            self.values: list[float] = []

        def observe(self, v: float) -> None:
            self.values.append(v)

    class DummyCounter:
        def __init__(self):
            self.count = 0

        def inc(self) -> None:
            self.count += 1

    alerts: list[tuple[list[float], list[float]]] = []
    hist = DummyHist()
    counter = DummyCounter()
    detector = ThresholdDriftDetector(
        ratio_threshold=1.5,
        metric=hist,
        alert_counter=counter,
        alert_func=lambda v, t: alerts.append((v, t)),
    )

    drift = detector.detect([2.0], [1.0])

    assert drift
    assert detector.values == [2.0]
    assert detector.thresholds == [1.0]
    assert hist.values == [2.0]
    assert counter.count == 1
    assert alerts and alerts[0][0] == [2.0]
