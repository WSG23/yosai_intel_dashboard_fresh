from flask import Flask

from src.api.metrics import metrics_bp, set_metrics_repository
from src.repository import InMemoryMetricsRepository


def create_app(repo: InMemoryMetricsRepository) -> Flask:
    app = Flask(__name__)
    set_metrics_repository(repo)
    app.register_blueprint(metrics_bp)
    return app


def test_performance_endpoint() -> None:
    repo = InMemoryMetricsRepository(performance={"t": 1})
    app = create_app(repo)
    client = app.test_client()
    resp = client.get("/v1/metrics/performance")
    assert resp.status_code == 200
    assert resp.get_json() == {"t": 1}


def test_drift_endpoint() -> None:
    repo = InMemoryMetricsRepository(drift={"prediction_drift": 0.3})
    app = create_app(repo)
    client = app.test_client()
    resp = client.get("/v1/metrics/drift")
    assert resp.status_code == 200
    assert resp.get_json() == {"prediction_drift": 0.3}


def test_feature_importance_endpoint() -> None:
    repo = InMemoryMetricsRepository(feature_importances={"a": 0.1})
    app = create_app(repo)
    client = app.test_client()
    resp = client.get("/v1/metrics/feature-importance")
    assert resp.status_code == 200
    assert resp.get_json() == {"a": 0.1}
