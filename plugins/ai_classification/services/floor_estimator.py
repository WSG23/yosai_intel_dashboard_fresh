"""Enhanced floor estimator with comprehensive pattern detection"""

import logging
import re
from collections import Counter
from typing import Any, Dict, List, Set

from yosai_intel_dashboard.src.adapters.api.plugins.ai_classification.config import (
    FloorEstimationConfig,
)
from yosai_intel_dashboard.src.adapters.api.plugins.ai_classification.database.csv_storage import (
    CSVStorageRepository,
)

logger = logging.getLogger(__name__)


class FloorEstimationService:
    """Enhanced floor estimation with multiple detection methods"""

    def __init__(
        self, repository: CSVStorageRepository, config: FloorEstimationConfig
    ) -> None:
        self.repository = repository
        self.config = config
        self.logger = logger

        # Comprehensive floor detection patterns
        self.floor_patterns = [
            # Direct floor indicators
            r"\b(\d+)(?:st|nd|rd|th)?\s*fl(?:oor)?\b",  # "2nd floor", "3 fl", etc.
            r"\bfl(?:oor)?\s*(\d+)\b",  # "floor 2", "fl 3"
            r"\bfloor[\s\-_]*(\d+)\b",  # "floor-2", "floor_3"
            r"\bf(\d+)\b",  # "f2", "f10"
            r"\b(\d+)f\b",  # "2f", "10f"
            r"\blevel[\s\-_]*(\d+)\b",  # "level 2", "level-3"
            r"\bl(\d+)\b",  # "l2", "l10"
            r"\b(\d+)l\b",  # "2l", "10l"
            # Building codes and references
            r"\b(\d+)-\d+\b",  # "2-101" (floor-room)
            r"\b(\d+)\.\d+\b",  # "2.101" (floor.room)
            r"\b(\d+)_\d+\b",  # "2_101" (floor_room)
            # Elevation/height indicators
            r"\b(\d+)(?:st|nd|rd|th)?\s*story\b",  # "2nd story"
            r"\bstory[\s\-_]*(\d+)\b",  # "story 2"
        ]

    def estimate_floors(self, data: List[Dict], session_id: str) -> Dict[str, Any]:
        """Enhanced floor estimation using multiple data sources and patterns"""
        try:
            if not data:
                result = {
                    "success": True,
                    "total_floors": 1,
                    "confidence": 0.0,
                    "method": "default",
                }
                self.repository.store_floor_estimation(session_id, result)
                return result

            all_text_fields = self._extract_text_fields(data)

            floor_detections = {
                "pattern_based": self._detect_floors_by_patterns(all_text_fields),
                "numeric_analysis": self._detect_floors_by_numeric_analysis(
                    all_text_fields
                ),
                "door_id_analysis": self._detect_floors_from_door_ids(data),
                "location_analysis": self._detect_floors_from_locations(data),
            }

            final_result = self._combine_floor_estimations(floor_detections)

            estimation_data = {
                "session_id": session_id,
                "total_floors": final_result["floors"],
                "confidence": final_result["confidence"],
                "method": final_result["method"],
                "details": floor_detections,
                "analyzed_records": len(data),
            }

            self.repository.store_floor_estimation(session_id, estimation_data)

            result = {
                "success": True,
                "total_floors": final_result["floors"],
                "confidence": final_result["confidence"],
                "method": final_result["method"],
            }

            self.logger.info(
                f"Floor estimation complete: {final_result['floors']} floors "
                f"(confidence: {final_result['confidence']:.1%}, method: {final_result['method']})"
            )

            return result

        except Exception as e:
            self.logger.error(f"Floor estimation failed: {e}")
            fallback_result = {
                "success": True,
                "total_floors": 1,
                "confidence": 0.0,
                "method": "error_fallback",
            }
            return fallback_result

    def _extract_text_fields(self, data: List[Dict]) -> List[str]:
        """Extract all text fields that might contain floor information"""
        text_fields = []
        for record in data:
            for key, value in record.items():
                if value and isinstance(value, (str, int, float)):
                    text_fields.append(str(value).lower().strip())
        return text_fields

    def _detect_floors_by_patterns(self, text_fields: List[str]) -> Dict[str, Any]:
        """Detect floors using regex patterns"""
        floor_numbers: Set[int] = set()
        pattern_matches = 0
        for text in text_fields:
            for pattern in self.floor_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    try:
                        floor_num = int(match.group(1))
                        if 1 <= floor_num <= 100:
                            floor_numbers.add(floor_num)
                            pattern_matches += 1
                    except (ValueError, IndexError):
                        continue
        max_floor = max(floor_numbers) if floor_numbers else 1
        confidence = (
            min(0.9, pattern_matches / len(text_fields)) if text_fields else 0.0
        )
        return {
            "floors": max_floor,
            "confidence": confidence,
            "found_floors": sorted(list(floor_numbers)),
            "pattern_matches": pattern_matches,
        }

    def _detect_floors_by_numeric_analysis(
        self, text_fields: List[str]
    ) -> Dict[str, Any]:
        """Detect floors by analyzing numeric patterns in identifiers"""
        potential_floors: List[int] = []
        for text in text_fields:
            numbers = re.findall(r"\b(\d{1,2})\b", text)
            for num_str in numbers:
                num = int(num_str)
                if 1 <= num <= 50:
                    potential_floors.append(num)
        if not potential_floors:
            return {"floors": 1, "confidence": 0.0}
        floor_counter = Counter(potential_floors)
        max_floor = max(potential_floors)
        unique_floors = len(set(potential_floors))
        confidence = (
            min(0.7, unique_floors / max(max_floor, 1) * 0.5) if max_floor > 1 else 0.0
        )
        return {
            "floors": max_floor,
            "confidence": confidence,
            "distribution": dict(floor_counter),
            "unique_floors": unique_floors,
        }

    def _detect_floors_from_door_ids(self, data: List[Dict]) -> Dict[str, Any]:
        """Analyze door IDs for floor patterns"""
        door_ids: List[str] = []
        possible_id_columns = [
            "door_id",
            "device_id",
            "door",
            "device",
            "location",
            "area",
            "reader",
        ]
        for record in data:
            for col in possible_id_columns:
                if col in record and record[col]:
                    door_ids.append(str(record[col]).lower())
                    break
        if not door_ids:
            return {"floors": 1, "confidence": 0.0}
        floor_numbers: Set[int] = set()
        for door_id in door_ids:
            for pattern in [
                r"(\d)(?:\d{2})",
                r"(\d+)[-_](?:\d+)",
                r"(\d+)f",
                r"floor(\d+)",
            ]:
                matches = re.finditer(pattern, door_id)
                for match in matches:
                    try:
                        floor_num = int(match.group(1))
                        if 1 <= floor_num <= 50:
                            floor_numbers.add(floor_num)
                    except (ValueError, IndexError):
                        continue
        max_floor = max(floor_numbers) if floor_numbers else 1
        confidence = (
            min(0.8, len(floor_numbers) / len(set(door_ids))) if door_ids else 0.0
        )
        return {
            "floors": max_floor,
            "confidence": confidence,
            "found_floors": sorted(list(floor_numbers)),
            "analyzed_doors": len(door_ids),
        }

    def _detect_floors_from_locations(self, data: List[Dict]) -> Dict[str, Any]:
        """Analyze location fields for floor information"""
        locations: List[str] = []
        location_columns = ["location", "area", "zone", "room", "office", "description"]
        for record in data:
            for col in location_columns:
                if col in record and record[col]:
                    locations.append(str(record[col]).lower())
        if not locations:
            return {"floors": 1, "confidence": 0.0}
        return self._detect_floors_by_patterns(locations)

    def _combine_floor_estimations(self, detections: Dict[str, Dict]) -> Dict[str, Any]:
        """Combine multiple detection methods with weighted confidence"""
        method_weights = {
            "pattern_based": 0.4,
            "door_id_analysis": 0.3,
            "location_analysis": 0.2,
            "numeric_analysis": 0.1,
        }
        weighted_results = []
        for method, result in detections.items():
            if result["confidence"] > 0:
                weight = method_weights.get(method, 0.1)
                weighted_score = result["confidence"] * weight
                weighted_results.append(
                    {
                        "method": method,
                        "floors": result["floors"],
                        "confidence": result["confidence"],
                        "weighted_score": weighted_score,
                    }
                )
        if not weighted_results:
            return {"floors": 1, "confidence": 0.0, "method": "no_detection"}
        best_result = max(weighted_results, key=lambda x: x["weighted_score"])
        floor_counts = Counter([r["floors"] for r in weighted_results])
        most_common_floors, frequency = floor_counts.most_common(1)[0]
        if frequency > 1:
            best_result["confidence"] = min(0.95, best_result["confidence"] * 1.2)
            best_result["method"] = f"{best_result['method']}_consensus"
        return {
            "floors": best_result["floors"],
            "confidence": best_result["confidence"],
            "method": best_result["method"],
        }
