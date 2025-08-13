from flask import Flask
from typing import Any, Dict

from src.api.metrics import metrics_bp, set_metrics_repository
from yosai_intel_dashboard.src.core.protocols.metrics import MetricsRepositoryProtocol


class StubMetricsRepository(MetricsRepositoryProtocol):
    def __init__(
        self,
        performance: Dict[str, Any] | None = None,
        drift: Dict[str, Any] | None = None,
        feature_importances: Dict[str, Any] | None = None,
    ) -> None:
        self._performance = performance or {}
        self._drift = drift or {}
        self._feature_importances = feature_importances or {}

    def get_performance_metrics(self) -> Dict[str, Any]:
        return self._performance

    def get_drift_data(self) -> Dict[str, Any]:
        return self._drift

    def get_feature_importances(self) -> Dict[str, Any]:
        return self._feature_importances


def create_app(repo: MetricsRepositoryProtocol) -> Flask:
    app = Flask(__name__)
    set_metrics_repository(repo)
    app.register_blueprint(metrics_bp)
    return app


def test_performance_endpoint() -> None:
    repo = StubMetricsRepository(performance={"t": 1})
    app = create_app(repo)
    client = app.test_client()
    resp = client.get("/v1/metrics/performance")
    assert resp.status_code == 200
    assert resp.get_json() == {"t": 1}


def test_drift_endpoint() -> None:
    repo = StubMetricsRepository(drift={"prediction_drift": 0.3})
    app = create_app(repo)
    client = app.test_client()
    resp = client.get("/v1/metrics/drift")
    assert resp.status_code == 200
    assert resp.get_json() == {"prediction_drift": 0.3}


def test_feature_importance_endpoint() -> None:
    repo = StubMetricsRepository(feature_importances={"a": 0.1})
    app = create_app(repo)
    client = app.test_client()
    resp = client.get("/v1/metrics/feature-importance")
    assert resp.status_code == 200
    assert resp.get_json() == {"a": 0.1}
