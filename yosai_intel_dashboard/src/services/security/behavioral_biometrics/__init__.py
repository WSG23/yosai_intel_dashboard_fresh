"""Behavioral biometric utilities."""

from __future__ import annotations

from typing import Sequence

from flask import Request

from .gait import GaitAnalyzer
from .interfaces import GaitCollector, KeystrokeCollector, KeystrokeEvent
from .keystroke import KeystrokeAnomalyDetector, extract_features

_keystroke_detector = KeystrokeAnomalyDetector()
_gait_analyzer = GaitAnalyzer()


def verify_behavioral_biometrics(request: Request) -> bool:
    """Verify request using keystroke dynamics and gait data.

    Data is expected via ``X-Keystroke-Metrics`` and ``X-Gait-Data`` headers as
    comma-separated floats. If no data is provided the check passes.
    """

    metrics = request.headers.get("X-Keystroke-Metrics")
    if metrics:
        try:
            features = [float(x) for x in metrics.split(" ")[0].split(",") if x]
        except ValueError:
            features = []
        if features and _keystroke_detector.is_anomaly(features):
            return False

    gait_data = request.headers.get("X-Gait-Data")
    if gait_data:
        try:
            sequence: Sequence[Sequence[float]] = [
                [float(x) for x in gait_data.split(" ")[0].split(",") if x]
            ]
        except ValueError:
            sequence = []
        if sequence and _gait_analyzer.is_anomaly(sequence):
            return False

    return True


__all__ = [
    "KeystrokeEvent",
    "KeystrokeCollector",
    "GaitCollector",
    "extract_features",
    "KeystrokeAnomalyDetector",
    "GaitAnalyzer",
    "verify_behavioral_biometrics",
]
