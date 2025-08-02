from flask import Flask

from src.api.metrics import metrics_bp, PERFORMANCE_METRICS, DRIFT_DATA, FEATURE_IMPORTANCES


def create_app():
    app = Flask(__name__)
    app.register_blueprint(metrics_bp)
    return app


def test_performance_endpoint():
    app = create_app()
    client = app.test_client()
    resp = client.get('/v1/metrics/performance')
    assert resp.status_code == 200
    assert resp.get_json() == PERFORMANCE_METRICS


def test_drift_endpoint():
    app = create_app()
    client = app.test_client()
    resp = client.get('/v1/metrics/drift')
    assert resp.status_code == 200
    assert resp.get_json() == DRIFT_DATA


def test_feature_importance_endpoint():
    app = create_app()
    client = app.test_client()
    resp = client.get('/v1/metrics/feature-importance')
    assert resp.status_code == 200
    assert resp.get_json() == FEATURE_IMPORTANCES
