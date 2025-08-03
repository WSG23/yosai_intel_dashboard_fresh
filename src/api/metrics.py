from flask import Blueprint, jsonify

from src.repository import (
    CachedMetricsRepository,
    InMemoryMetricsRepository,
    MetricsRepository,
)

metrics_bp = Blueprint("metrics", __name__, url_prefix="/v1/metrics")

_metrics_repo: MetricsRepository = CachedMetricsRepository(InMemoryMetricsRepository())


def set_metrics_repository(
    repo: MetricsRepository, *, use_cache: bool = True, ttl: int = 60
) -> None:
    """Inject a metrics repository implementation.

    Parameters
    ----------
    repo:
        The underlying metrics repository.
    use_cache:
        If ``True`` (default), wrap ``repo`` in :class:`CachedMetricsRepository`.
    ttl:
        Cache expiration in seconds when ``use_cache`` is enabled.
    """
    global _metrics_repo
    _metrics_repo = CachedMetricsRepository(repo, ttl=ttl) if use_cache else repo


@metrics_bp.get("/performance")
def get_performance_metrics():
    """Return performance metrics from the repository."""
    return jsonify(_metrics_repo.get_performance_metrics())


@metrics_bp.get("/drift")
def get_drift_data():
    """Return drift statistics from the repository."""
    return jsonify(_metrics_repo.get_drift_data())


@metrics_bp.get("/feature-importance")
def get_feature_importances():
    """Return feature importances from the repository."""
    return jsonify(_metrics_repo.get_feature_importances())


__all__ = ["metrics_bp", "set_metrics_repository"]
