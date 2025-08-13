from __future__ import annotations

"""Bias detection utilities using fairness metrics."""

import logging
from typing import Any, Dict, Iterable

from optional_dependencies import import_optional

MetricFrame = import_optional("fairlearn.metrics.MetricFrame")
selection_rate = import_optional("fairlearn.metrics.selection_rate")
accuracy_score = import_optional("sklearn.metrics.accuracy_score")

logger = logging.getLogger(__name__)


def detect_bias(
    y_true: Iterable[Any],
    y_pred: Iterable[Any],
    sensitive_features: Iterable[Any],
) -> Dict[str, Any]:
    """Compute basic fairness metrics.

    Parameters
    ----------
    y_true, y_pred:
        Ground truth and predicted labels.
    sensitive_features:
        Iterable identifying the sensitive group for each sample.

    Returns
    -------
    dict
        Dictionary with overall metrics, per-group metrics and metric
        differences. Returns an empty dict if required dependencies are
        missing.
    """

    if not (MetricFrame and selection_rate and accuracy_score):
        logger.warning("fairlearn and scikit-learn are required for bias detection")
        return {}

    frame = MetricFrame(
        metrics={"accuracy": accuracy_score, "selection_rate": selection_rate},
        y_true=list(y_true),
        y_pred=list(y_pred),
        sensitive_features=list(sensitive_features),
    )
    result: Dict[str, Any] = {
        "overall": frame.overall.to_dict(),
        "by_group": frame.by_group.to_dict(),
    }
    try:  # pragma: no cover - depends on fairlearn implementation
        result["difference"] = frame.difference().to_dict()
    except Exception:  # pragma: no cover
        logger.debug("difference metric not available", exc_info=True)
    return result


__all__ = ["detect_bias"]
