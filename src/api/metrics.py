from flask import Blueprint, jsonify

metrics_bp = Blueprint('metrics', __name__, url_prefix='/v1/metrics')

# Sample static data for demonstration purposes
PERFORMANCE_METRICS = {'throughput': 100, 'latency_ms': 50}
DRIFT_DATA = {'prediction_drift': 0.02, 'feature_drift': {'age': 0.01}}
FEATURE_IMPORTANCES = {'age': 0.3, 'income': 0.2, 'score': 0.1}

@metrics_bp.get('/performance')
def get_performance_metrics():
    """Return sample performance metrics."""
    return jsonify(PERFORMANCE_METRICS)

@metrics_bp.get('/drift')
def get_drift_data():
    """Return sample drift statistics."""
    return jsonify(DRIFT_DATA)

@metrics_bp.get('/feature-importance')
def get_feature_importances():
    """Return sample feature importances."""
    return jsonify(FEATURE_IMPORTANCES)

__all__ = ['metrics_bp']
