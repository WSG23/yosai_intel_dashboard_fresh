"""Keystroke dynamics feature extraction and anomaly detection."""

from __future__ import annotations

from typing import Iterable, List

from .interfaces import KeystrokeEvent

try:  # pragma: no cover - dependency availability
    from sklearn.ensemble import IsolationForest
except Exception:  # pragma: no cover - handle missing dependency
    IsolationForest = None  # type: ignore[misc]


def extract_features(events: Iterable[KeystrokeEvent]) -> List[float]:
    """Return dwell and flight time features from keystroke events.

    Dwell times measure how long a key is pressed. Flight times measure the time
    between releasing one key and pressing the next.
    """

    events = list(events)
    if not events:
        return []

    dwell_times = [e.release_time - e.press_time for e in events]
    flight_times = [
        events[i + 1].press_time - events[i].release_time
        for i in range(len(events) - 1)
    ]
    return dwell_times + flight_times


class KeystrokeAnomalyDetector:
    """Detect anomalous typing rhythm using ``IsolationForest``."""

    def __init__(self) -> None:
        self.model = (
            IsolationForest(n_estimators=100, contamination=0.1)
            if IsolationForest
            else None
        )
        self._fitted = False

    def fit(self, baseline: List[float]) -> None:
        """Fit the model on baseline features for a user."""
        if self.model is None or not baseline:
            return
        self.model.fit([baseline])
        self._fitted = True

    def is_anomaly(self, features: List[float]) -> bool:
        """Return ``True`` if ``features`` deviate from the baseline."""
        if self.model is None or not features:
            return False
        if not self._fitted:
            # First observation becomes the baseline.
            self.fit(features)
            return False
        return self.model.predict([features])[0] == -1
