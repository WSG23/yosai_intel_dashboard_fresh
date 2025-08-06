"""AI powered column mapping service"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from yosai_intel_dashboard.src.adapters.api.plugins.ai_classification.config import (
    ColumnMappingConfig,
)
from yosai_intel_dashboard.src.adapters.api.plugins.ai_classification.database.ai_models import (
    ColumnClassifier,
)
from yosai_intel_dashboard.src.adapters.api.plugins.ai_classification.database.csv_storage import (
    CSVStorageRepository,
)

from .base import RepositoryConfigService


class ColumnMappingService(RepositoryConfigService):
    """Suggest mappings from CSV headers to standard fields."""

    STANDARD_FIELDS = {
        "timestamp": [
            "time",
            "date",
            "datetime",
            "timestamp",
            "event_time",
            "created_at",
        ],
        "user_id": [
            "user",
            "id",
            "card",
            "employee",
            "person_id",
            "user_name",
            "badge_id",
            "person",
        ],
        "location": [
            "location",
            "door",
            "room",
            "area",
            "door_id",
            "access_location",
            "access_point",
        ],
        "access_type": [
            "access",
            "type",
            "action",
            "entry",
            "exit",
            "result",
            "access_result",
            "status",
        ],
    }

    def __init__(
        self, repository: CSVStorageRepository, config: ColumnMappingConfig
    ) -> None:
        super().__init__(repository, config)
        self.classifier: Optional[ColumnClassifier] = None
        if self.config.learning_enabled:
            self.classifier = ColumnClassifier(
                self.config.model_path, self.config.vectorizer_path
            )
            if not self.classifier.is_ready():
                self.logger.warning("ML model not found, using heuristics")

    def map_columns(self, headers: List[str], session_id: str) -> Dict[str, Any]:
        mapping: Dict[str, str] = {}
        confidence: Dict[str, float] = {}

        for header in headers:
            field, score = self._predict_field_type(header)
            if field:
                mapping[header] = field
                confidence[header] = score

        mapping_data = {
            "session_id": session_id,
            "suggested_mapping": mapping,
            "confidence_scores": confidence,
            "status": "pending_confirmation",
            "created_at": datetime.now().isoformat(),
        }
        self.repository.store_column_mapping(session_id, mapping_data)

        return {
            "success": True,
            "suggested_mapping": mapping,
            "confidence_scores": confidence,
            "requires_confirmation": True,
        }

    def confirm_mapping(self, mapping: Dict[str, str], session_id: str) -> bool:
        try:
            confirmed = {
                "session_id": session_id,
                "confirmed_mapping": mapping,
                "status": "confirmed",
                "confirmed_at": datetime.now().isoformat(),
            }
            self.repository.update_column_mapping(session_id, confirmed)
            return True
        except Exception as exc:
            self.logger.error("mapping confirmation failed: %s", exc)
            return False

    def get_enhanced_mapping_with_fallbacks(
        self, headers: List[str], session_id: str
    ) -> Dict[str, Any]:
        """Enhanced mapping with intelligent fallbacks for common issues"""

        # First, get AI predictions
        ai_result = self.map_columns(headers, session_id)
        suggested_mapping = ai_result.get("suggested_mapping", {})
        confidence_scores = ai_result.get("confidence_scores", {})

        # Apply intelligent fallbacks for unmapped critical columns
        enhanced_mapping = suggested_mapping.copy()
        enhanced_confidence = confidence_scores.copy()

        # Critical column fallbacks
        critical_mappings = {
            "person_id": ["user_name", "person_name", "badge_holder", "employee_name"],
            "door_id": ["access_location", "location_name", "door_name", "entry_point"],
            "access_result": ["result", "status", "outcome"],
            "timestamp": ["event_time", "datetime", "time_stamp"],
        }

        for target_field, candidate_headers in critical_mappings.items():
            # If AI didn't map this critical field, try fallbacks
            if target_field not in suggested_mapping.values():
                for header in headers:
                    if header.lower() in [c.lower() for c in candidate_headers]:
                        enhanced_mapping[header] = target_field
                        enhanced_confidence[header] = (
                            0.85  # High confidence for direct matches
                        )
                        self.logger.info(
                            f"Applied fallback mapping: '{header}' -> '{target_field}'"
                        )
                        break

        # Store enhanced mapping
        enhanced_data = {
            "session_id": session_id,
            "suggested_mapping": enhanced_mapping,
            "confidence_scores": enhanced_confidence,
            "ai_enhanced": True,
            "fallbacks_applied": len(enhanced_mapping) - len(suggested_mapping),
            "status": "pending_confirmation",
            "created_at": datetime.now().isoformat(),
        }
        self.repository.store_column_mapping(session_id, enhanced_data)

        return {
            "success": True,
            "suggested_mapping": enhanced_mapping,
            "confidence_scores": enhanced_confidence,
            "requires_confirmation": True,
            "ai_enhanced": True,
            "fallbacks_applied": len(enhanced_mapping) - len(suggested_mapping),
        }

    def _predict_field_type_heuristic(self, header: str) -> Tuple[Optional[str], float]:
        h = header.lower()
        best_field = None
        best_score = 0.0

        for field, keywords in self.STANDARD_FIELDS.items():
            for kw in keywords:
                if kw in h:
                    score = len(kw) / len(h)
                    if score > best_score:
                        best_score = score
                        best_field = field
        if best_score < self.config.min_confidence_threshold:
            return None, 0.0
        return best_field, best_score

    def _predict_field_type_ml(self, header: str) -> Tuple[Optional[str], float]:
        if not self.classifier or not self.classifier.is_ready():
            return self._predict_field_type_heuristic(header)
        try:
            prediction = self.classifier.predict([header])[0]
            field, score = prediction
            if score >= self.config.min_confidence_threshold:
                return field, score
        except Exception as exc:
            self.logger.error("ml prediction failed: %s", exc)
        return self._predict_field_type_heuristic(header)

    def _predict_field_type(self, header: str) -> Tuple[Optional[str], float]:
        if self.classifier and self.classifier.is_ready():
            return self._predict_field_type_ml(header)
        return self._predict_field_type_heuristic(header)
