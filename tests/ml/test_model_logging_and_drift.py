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

from intel_analysis_service.ml import AnomalyDetector, RiskScorer


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
