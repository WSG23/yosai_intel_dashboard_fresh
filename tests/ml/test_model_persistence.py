import sys
import types

import pandas as pd

# Stub opentelemetry and trace modules so imports succeed without the real package.
class _Span:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _Tracer:
    def start_as_current_span(self, name):
        return _Span()


trace_stub = types.ModuleType("trace")
trace_stub.get_tracer = lambda name: _Tracer()
opentelemetry_stub = types.ModuleType("opentelemetry")
opentelemetry_stub.trace = trace_stub
sys.modules["trace"] = trace_stub
sys.modules["opentelemetry"] = opentelemetry_stub
sys.modules["opentelemetry.trace"] = trace_stub

from intel_analysis_service.ml import (
    AnomalyDetector,
    RiskScorer,
    ModelRegistry,
    load_anomaly_model,
    load_risk_model,
)


def test_anomaly_model_round_trip(tmp_path):
    reg = ModelRegistry(tmp_path)
    ts = pd.date_range("2024-01-01", periods=5, freq="D")
    df = pd.DataFrame({"timestamp": ts, "value": 1.0})
    model = AnomalyDetector(factor=1.0).fit(df)
    meta = model.save(reg, version="v1")
    loaded = load_anomaly_model(meta.version, reg)
    preds = loaded.predict(pd.DataFrame({"timestamp": [ts[0]], "value": [1.0]}))
    assert "is_anomaly" in preds


def test_risk_model_round_trip(tmp_path):
    reg = ModelRegistry(tmp_path)
    ts = pd.date_range("2024-01-01", periods=5, freq="D")
    df = pd.DataFrame({"timestamp": ts, "a": 1.0})
    model = RiskScorer({"a": 1.0}).fit(df)
    meta = model.save(reg, version="v1")
    loaded = load_risk_model(meta.version, reg)
    result = loaded.score(pd.DataFrame({"timestamp": [ts[0]], "a": [1.0]}))
    assert "is_risky" in result
