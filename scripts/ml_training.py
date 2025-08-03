"""Schedule training and evaluation jobs for context models."""

from __future__ import annotations

import logging
import sched
import time
from typing import List, Tuple

import pandas as pd

from intel_analysis_service.ml import (
    AnomalyDetector,
    RiskScorer,
    build_context_features,
)

LOG = logging.getLogger(__name__)

TRAIN_INTERVAL = 24 * 60 * 60  # daily
EVAL_INTERVAL = 60 * 60  # hourly

scheduler = sched.scheduler(time.time, time.sleep)


def _generate_sample_events(days: int = 7) -> Tuple[pd.DataFrame, ...]:
    """Generate synthetic event data for demo purposes."""
    ts = pd.date_range(pd.Timestamp.now().normalize(), periods=days, freq="D")
    base = pd.DataFrame({"timestamp": ts})
    weather = base.assign(weather=1)
    events = base.assign(events=0)
    transport = base.assign(transport=0)
    social = base.assign(social=0)
    infra = base.assign(infra=0)
    return weather, events, transport, social, infra


def train_models() -> Tuple[AnomalyDetector, RiskScorer]:
    """Train anomaly detection and risk scoring models using sample data."""
    weather, events, transport, social, infra = _generate_sample_events()
    features = build_context_features(weather, events, transport, social, infra)
    features["value"] = features.drop(columns=["timestamp"]).sum(axis=1)
    detector = AnomalyDetector().fit(features[["timestamp", "value"]])
    scorer = RiskScorer({c: 1.0 for c in features.columns if c != "timestamp"}).fit(features)
    LOG.info("Trained models with thresholds: detector=%s scorer=%s", detector.thresholds, scorer.thresholds)
    return detector, scorer


def evaluate_models(detector: AnomalyDetector, scorer: RiskScorer) -> dict:
    """Evaluate models on fresh synthetic data and return metrics."""
    weather, events, transport, social, infra = _generate_sample_events()
    features = build_context_features(weather, events, transport, social, infra)
    features["value"] = features.drop(columns=["timestamp"]).sum(axis=1)
    anomalies = detector.predict(features[["timestamp", "value"]])
    risks = scorer.score(features)
    metrics = {
        "anomalies": int(anomalies["is_anomaly"].sum()),
        "high_risk": int(risks["is_risky"].sum()),
    }
    LOG.info("Evaluation metrics: %s", metrics)
    return metrics


def schedule_jobs(
    train_interval: int = TRAIN_INTERVAL,
    eval_interval: int = EVAL_INTERVAL,
    run_once: bool = False,
) -> List[Tuple[str, object]]:
    """Schedule training and evaluation jobs.

    When ``run_once`` is True the jobs are executed immediately once and the
    results are returned which makes the function convenient for testing.
    """

    results: List[Tuple[str, object]] = []

    detector: AnomalyDetector | None = None
    scorer: RiskScorer | None = None

    def train_wrapper() -> None:
        nonlocal detector, scorer
        detector, scorer = train_models()
        results.append(("train", (detector, scorer)))
        if not run_once:
            scheduler.enter(train_interval, 1, train_wrapper)

    def eval_wrapper() -> None:
        if detector is None or scorer is None:
            LOG.warning("Models not trained yet; skipping evaluation")
            if not run_once:
                scheduler.enter(eval_interval, 1, eval_wrapper)
            return
        metrics = evaluate_models(detector, scorer)
        results.append(("eval", metrics))
        if not run_once:
            scheduler.enter(eval_interval, 1, eval_wrapper)

    scheduler.enter(0, 1, train_wrapper)
    scheduler.enter(0, 1, eval_wrapper)
    scheduler.run()
    return results


if __name__ == "__main__":  # pragma: no cover - CLI
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    schedule_jobs()
