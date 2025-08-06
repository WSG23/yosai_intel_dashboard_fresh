"""Behavioral biometric utilities.

This module provides a lightweight pipeline for collecting keystroke and gait
metrics, training per-user models and verifying requests. Only minimal data is
stored and a consent header (``X-Biometric-Consent``) is required before any
training occurs, satisfying GDPR/APPI requirements. A simple in-memory store is
used with a time based retention policy.
"""

from __future__ import annotations

from dataclasses import dataclass
from time import time
from typing import Dict, Sequence

from typing import Any

try:  # pragma: no cover - Flask may not be installed during tests
    from flask import Request, session
except Exception:  # pragma: no cover - fallback for minimal environments
    Request = Any  # type: ignore[misc,assignment]
    session = {}  # type: ignore[assignment]

from .interfaces import GaitCollector, KeystrokeCollector, KeystrokeEvent

# Inline lightweight gait and keystroke models to avoid optional heavy
# dependencies during tests.


class GaitAnalyzer:
    """Detect gait anomalies using a baseline mean vector."""

    def __init__(self, threshold: float = 0.2) -> None:
        self.baseline: list[float] | None = None
        self.threshold = threshold

    def fit(self, sequence: Sequence[Sequence[float]]) -> None:
        if not sequence:
            return
        columns = list(zip(*sequence))
        self.baseline = [sum(col) / len(col) for col in columns]

    def is_anomaly(self, sequence: Sequence[Sequence[float]]) -> bool:
        if self.baseline is None or not sequence:
            return False
        columns = list(zip(*sequence))
        current = [sum(col) / len(col) for col in columns]
        deviation = sum(abs(a - b) for a, b in zip(self.baseline, current)) / len(current)
        return deviation > self.threshold


# Inline a lightweight keystroke feature extractor and anomaly detector to avoid
# importing optional heavy dependencies during tests.

def extract_features(events: Sequence[KeystrokeEvent]) -> list[float]:
    """Return dwell and flight time features from keystroke events."""

    events = list(events)
    if not events:
        return []
    dwell = [e.release_time - e.press_time for e in events]
    flight = [
        events[i + 1].press_time - events[i].release_time
        for i in range(len(events) - 1)
    ]
    return dwell + flight


class KeystrokeAnomalyDetector:
    """Detect anomalies using a simple distance from baseline."""

    def __init__(self, threshold: float = 0.1) -> None:
        self.baseline: list[float] | None = None
        self.threshold = threshold

    def fit(self, features: list[float]) -> None:
        if features:
            self.baseline = features[:]

    def is_anomaly(self, features: list[float]) -> bool:
        if not features or self.baseline is None:
            return False
        diff = sum(abs(a - b) for a, b in zip(self.baseline, features)) / len(
            features
        )
        return diff > self.threshold


# ---------------------------------------------------------------------------
# Data capture helpers

def capture_keystroke_vector(collector: KeystrokeCollector) -> list[float]:
    """Collect keystroke events and return extracted features."""

    return extract_features(collector.collect())


def capture_gait_sequence(collector: GaitCollector) -> Sequence[Sequence[float]]:
    """Collect gait measurements as a sequence suitable for ``GaitAnalyzer``."""

    return [list(collector.collect())]


# ---------------------------------------------------------------------------
# Per-user model storage with retention policy


@dataclass
class _UserModel:
    keystroke: KeystrokeAnomalyDetector
    gait: GaitAnalyzer
    updated: float


_MODELS: Dict[str, _UserModel] = {}


def purge_expired_models(max_age: float) -> None:
    """Remove user models older than ``max_age`` seconds."""

    now = time()
    stale = [uid for uid, model in _MODELS.items() if now - model.updated > max_age]
    for uid in stale:
        _MODELS.pop(uid, None)


# ---------------------------------------------------------------------------

def verify_behavioral_biometrics(request: Request, retention_seconds: int = 86400) -> bool:
    """Verify request using keystroke dynamics and gait data.

    Data is expected via ``X-Keystroke-Metrics`` and ``X-Gait-Data`` headers as
    comma-separated floats. ``X-Biometric-Consent`` must be ``"true"`` to allow
    model training or verification. If consent is missing the check passes and
    no data is stored.
    """

    purge_expired_models(retention_seconds)

    user_id = session.get("user_id")
    consent = request.headers.get("X-Biometric-Consent", "false").lower() == "true"
    if not user_id or not consent:
        return True

    model = _MODELS.get(user_id)
    if model is None:
        model = _UserModel(KeystrokeAnomalyDetector(), GaitAnalyzer(), time())
        _MODELS[user_id] = model
    else:
        model.updated = time()

    metrics = request.headers.get("X-Keystroke-Metrics")
    if metrics:
        try:
            features = [float(x) for x in metrics.split(" ")[0].split(",") if x]
        except ValueError:
            features = []
        if features:
            if model.keystroke.baseline is None:
                model.keystroke.fit(features)
            elif model.keystroke.is_anomaly(features):
                return False

    gait_data = request.headers.get("X-Gait-Data")
    if gait_data:
        try:
            sequence: Sequence[Sequence[float]] = [
                [float(x) for x in gait_data.split(" ")[0].split(",") if x]
            ]
        except ValueError:
            sequence = []
        if sequence:
            if model.gait.baseline is None:
                model.gait.fit(sequence)
            elif model.gait.is_anomaly(sequence):
                return False

    return True


__all__ = [
    "KeystrokeEvent",
    "KeystrokeCollector",
    "GaitCollector",
    "capture_keystroke_vector",
    "capture_gait_sequence",
    "extract_features",
    "KeystrokeAnomalyDetector",
    "GaitAnalyzer",
    "purge_expired_models",
    "verify_behavioral_biometrics",
]
