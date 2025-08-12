from __future__ import annotations

from flask import Blueprint, jsonify
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from yosai_intel_dashboard.src.core.protocols.metrics import MetricsRepositoryProtocol

metrics_bp = Blueprint("metrics", __name__, url_prefix="/v1/metrics")

_metrics_repo: MetricsRepositoryProtocol | None = None


def set_metrics_repository(repo: MetricsRepositoryProtocol) -> None:
    """Inject a metrics repository implementation."""
    global _metrics_repo
    _metrics_repo = repo


def _get_repo() -> MetricsRepositoryProtocol:
    if _metrics_repo is None:  # pragma: no cover - safety check
        raise RuntimeError("Metrics repository not configured")
    return _metrics_repo


@metrics_bp.get("/performance")
def get_performance_metrics():
    """Return performance metrics from the repository."""
    return jsonify(_get_repo().get_performance_metrics())


@metrics_bp.get("/drift")
def get_drift_data():
    """Return drift statistics from the repository."""
    return jsonify(_get_repo().get_drift_data())


@metrics_bp.get("/feature-importance")
def get_feature_importances():
    """Return feature importances from the repository."""
    return jsonify(_get_repo().get_feature_importances())


__all__ = ["metrics_bp", "set_metrics_repository"]
