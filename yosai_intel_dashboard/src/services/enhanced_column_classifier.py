"""
Enhanced ML column classifier with heuristic fallbacks.
Replaces plugins/ai_classification/services/column_mapper.py
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np


class EnhancedColumnClassifier:
    """ML-powered column classifier with heuristic fallbacks."""

    def __init__(
        self,
        model_path: str = "data/column_model.joblib",
        confidence_threshold: float = 0.7,
    ):
        self.model_path = Path(model_path)
        self.vectorizer_path = Path("data/column_vectorizer.joblib")
        self.confidence_threshold = confidence_threshold
        self.classifier: Optional[Any] = None
        self.vectorizer: Optional[Any] = None
        self.logger = logging.getLogger(__name__)

        # Standard field patterns for heuristic fallback
        #
        # User and device identifiers are intentionally matched only against
        # specific aliases to avoid overly broad detections:
        #   - ``user_id``: matches "person", "user", or "employee"
        #   - ``device_id``: matches "device" or "door"
        self.field_patterns = {
            "device_id": [r"device", r"door"],
            "timestamp": [r"time", r"date", r"when", r"stamp", r"created"],
            "user_id": [r"person", r"user", r"employee"],
            "event_type": [r"event", r"action", r"type", r"status", r"result"],
            "floor": [r"floor", r"level", r"story"],
            "location": [r"location", r"place", r"area", r"zone"],
        }

        # Precompile regex patterns for faster heuristic matching
        self._compiled_patterns = [
            (re.compile(pattern), field)
            for field, patterns in self.field_patterns.items()
            for pattern in patterns
        ]

        # Try to load ML model
        self._load_model()

    def _load_model(self) -> bool:
        """Load trained ML model and vectorizer."""
        try:
            if self.model_path.exists() and self.vectorizer_path.exists():
                self.classifier = joblib.load(self.model_path)
                self.vectorizer = joblib.load(self.vectorizer_path)
                self.logger.info("ML model loaded successfully")
                return True
        except Exception as e:
            self.logger.warning(f"Could not load ML model: {e}")

        self.logger.info("Using heuristic-only mode")
        return False

    def predict_column_mappings(self, headers: List[str]) -> Dict[str, Any]:
        """Predict field mappings for column headers."""
        if self.classifier and self.vectorizer:
            return self._predict_ml_batch(headers)
        else:
            return self._predict_heuristic_batch(headers)

    def _predict_ml_batch(self, headers: List[str]) -> Dict[str, Any]:
        """ML-based batch prediction with heuristic fallback."""
        mappings: Dict[str, str] = {}
        confidence_scores: Dict[str, float] = {}
        method = "ml_with_fallback"

        try:
            assert self.vectorizer is not None, "Vectorizer is not loaded"
            assert self.classifier is not None, "Classifier is not loaded"
            features = self.vectorizer.transform(headers)
            predictions = self.classifier.predict_proba(features)

            for i, header in enumerate(headers):
                class_idx = int(np.argmax(predictions[i]))
                confidence = float(predictions[i][class_idx])
                predicted_field = str(self.classifier.classes_[class_idx])

                if confidence >= self.confidence_threshold:
                    mappings[header] = predicted_field
                    confidence_scores[header] = confidence
                else:
                    heuristic_field, heuristic_conf = self._predict_heuristic_single(
                        header
                    )
                    if heuristic_field:
                        mappings[header] = heuristic_field
                        confidence_scores[header] = heuristic_conf
        except Exception as e:
            self.logger.error(f"ML prediction failed: {e}")
            return self._predict_heuristic_batch(headers)

        return {
            "mappings": mappings,
            "confidence_scores": confidence_scores,
            "method": method,
            "ml_available": True,
        }

    def _predict_heuristic_batch(self, headers: List[str]) -> Dict[str, Any]:
        """Pure heuristic prediction for all headers."""
        mappings: Dict[str, str] = {}
        confidence_scores: Dict[str, float] = {}

        for header in headers:
            field, confidence = self._predict_heuristic_single(header)
            if field:
                mappings[header] = field
                confidence_scores[header] = confidence

        return {
            "mappings": mappings,
            "confidence_scores": confidence_scores,
            "method": "heuristic_only",
            "ml_available": False,
        }

    def _predict_heuristic_single(self, header: str) -> Tuple[Optional[str], float]:
        """Single header heuristic prediction."""
        header_lower = header.lower().strip()
        best_field = None
        best_score = 0.0

        threshold = 0.3
        for regex, field in self._compiled_patterns:
            if regex.search(header_lower):
                score = len(regex.pattern) / len(header_lower)
                if score > best_score:
                    best_field = field
                    best_score = score
                    if best_score >= threshold:
                        break

        if best_score >= threshold:
            return best_field, min(best_score + 0.1, 0.8)
        return None, 0.0

    def is_ml_available(self) -> bool:
        """Check if ML model is loaded and available."""
        return self.classifier is not None and self.vectorizer is not None


def create_column_classifier() -> EnhancedColumnClassifier:
    """Factory function for column classifier."""
    return EnhancedColumnClassifier()
