"""Device mapping and classification service - replaces entry classifier"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, List, Optional

from yosai_intel_dashboard.src.adapters.api.plugins.ai_classification.config import (
    EntryClassificationConfig,
)
from yosai_intel_dashboard.src.adapters.api.plugins.ai_classification.database.csv_storage import (
    CSVStorageRepository,
)

from .base import RepositoryConfigService


class EntryClassificationService(RepositoryConfigService):
    """Device mapping for floor, entry/exit, elevator, stairwell, fire escape, and security level"""

    # Security level keywords (device name -> security adjustment)
    SECURITY_KEYWORDS = {
        "high": [
            "server",
            "data",
            "telecom",
            "electrical",
            "mechanical",
            "executive",
            "ceo",
            "finance",
            "hr",
            "secure",
            "restricted",
        ],
        "medium": [
            "office",
            "meeting",
            "conference",
            "storage",
            "supply",
            "break",
            "kitchen",
        ],
        "low": [
            "lobby",
            "entrance",
            "public",
            "visitor",
            "reception",
            "restroom",
            "hallway",
            "corridor",
        ],
    }

    # Enhanced floor detection patterns with zero-padding and F-prefix support
    FLOOR_PATTERNS = [
        # Standard floor indicators
        r"\b(\d+)(?:st|nd|rd|th)?\s*fl(?:oor)?\b",  # "2nd floor", "3 fl"
        r"\bfl(?:oor)?\s*(\d+)\b",  # "floor 2", "fl 3"
        r"\blevel[\s\-_]*(\d+)\b",  # "level 2", "level-3"
        # F-prefix patterns that handle codes like F03, F04, etc.
        r"\bf(\d+)\b",  # "f2", "f10", "f03", "f04"
        r"\b(\d+)f\b",  # "2f", "10f"
        # Building room patterns
        r"\b(\d+)-\d+\b",  # "2-101" (floor-room)
        r"\b(\d+)\.\d+\b",  # "2.101" (floor.room)
        r"\b(\d+)_\d+\b",  # "2_101" (floor_room)
        # Zero-padded patterns (NEW - handles F03, F04)
        r"\bf0*(\d+)\b",  # "f01", "f03", "f004"
        r"\b(\d+)(?=\d{2,3})\b",  # "301" -> "3", "1205" -> "12"
    ]

    def __init__(
        self, repository: CSVStorageRepository, config: EntryClassificationConfig
    ) -> None:
        super().__init__(repository, config)

    def classify_entries(self, data: List[Dict], session_id: str) -> List[Dict]:
        """Main entry point - now does device mapping instead of simple entry classification"""
        device_mappings = self._map_devices(data)

        # Store device mappings
        mapping_data = {
            "device_mappings": device_mappings,
            "requires_verification": True,
            "created_at": "timestamp",
        }
        self.repository.store_entry_classification(session_id, mapping_data)

        return data  # Return original data, mappings stored separately

    def _map_devices(self, data: List[Dict]) -> Dict[str, Dict]:
        """Extract and analyze devices from data"""
        devices = self._extract_unique_devices(data)
        device_mappings = {}

        for device_name in devices:
            attributes = self._analyze_device(device_name)
            device_mappings[device_name] = attributes

        return device_mappings

    def _extract_unique_devices(self, data: List[Dict]) -> List[str]:
        """Extract unique device names from data"""
        devices = set()
        device_columns = ["door_id", "device_id", "location", "area", "device", "door"]

        for row in data:
            for col in device_columns:
                if col in row and row[col]:
                    devices.add(str(row[col]))
        return list(devices)

    def _analyze_device(self, device_name: str) -> Dict[str, Any]:
        """Analyze single device and return attributes"""
        device_lower = device_name.lower()

        return {
            "floor_number": self._detect_floor(device_lower),
            "is_entry": self._detect_entry(device_lower),
            "is_exit": self._detect_exit(device_lower),
            "is_elevator": self._detect_elevator(device_lower),
            "is_stairwell": self._detect_stairwell(device_lower),
            "is_fire_escape": self._detect_fire_escape(device_lower),
            "security_level": self._predict_security_level(device_lower),
            "confidence": self._calculate_confidence(device_lower),
            "ai_generated": True,
            "manually_edited": False,
        }

    def _detect_floor(self, device_name: str) -> Optional[int]:
        """Enhanced floor detection with zero-padding support"""
        for pattern in self.FLOOR_PATTERNS:
            matches = re.finditer(pattern, device_name, re.IGNORECASE)
            for match in matches:
                try:
                    floor_num = int(match.group(1))
                    # Handle zero-padded numbers like F03 -> floor 3
                    if "f0" in device_name.lower() and floor_num < 10:
                        return floor_num
                    # Standard range check
                    if 1 <= floor_num <= 50:
                        return floor_num
                except (ValueError, IndexError):
                    continue
        return None

    def _detect_entry(self, device_name: str) -> bool:
        """Detect if device is an entry point"""
        entry_terms = [
            "entry",
            "entrance",
            "enter",
            "in",
            "lobby",
            "reception",
            "front",
            "main",
        ]
        return any(term in device_name for term in entry_terms)

    def _detect_exit(self, device_name: str) -> bool:
        """Detect if device is an exit point"""
        exit_terms = ["exit", "egress", "out", "emergency", "fire", "evacuation"]
        # Main areas are usually both entry and exit
        main_terms = ["main", "lobby", "reception"]
        return any(term in device_name for term in exit_terms + main_terms)

    def _detect_elevator(self, device_name: str) -> bool:
        """Detect elevator access"""
        return any(term in device_name for term in ["elevator", "lift", "elev"])

    def _detect_stairwell(self, device_name: str) -> bool:
        """Detect stairwell access"""
        return any(
            term in device_name for term in ["stair", "stairs", "stairwell", "steps"]
        )

    def _detect_fire_escape(self, device_name: str) -> bool:
        """Detect fire escape"""
        return any(
            term in device_name
            for term in ["fire", "emergency", "evacuation", "escape"]
        )

    def _predict_security_level(self, device_name: str) -> int:
        """Predict security level 0-10"""
        base_level = 2

        # Check high security terms
        if any(term in device_name for term in self.SECURITY_KEYWORDS["high"]):
            return min(9, base_level + 6)

        # Check medium security terms
        if any(term in device_name for term in self.SECURITY_KEYWORDS["medium"]):
            return min(6, base_level + 2)

        # Check low security terms
        if any(term in device_name for term in self.SECURITY_KEYWORDS["low"]):
            return max(0, base_level - 2)

        return base_level

    def _calculate_confidence(self, device_name: str) -> float:
        """Calculate confidence score for predictions"""
        confidence_factors = []

        # Floor detection confidence
        floor_detected = any(
            re.search(pattern, device_name) for pattern in self.FLOOR_PATTERNS
        )
        confidence_factors.append(0.9 if floor_detected else 0.3)

        # Security level confidence
        all_security_terms = sum(self.SECURITY_KEYWORDS.values(), [])
        security_match = any(term in device_name for term in all_security_terms)
        confidence_factors.append(0.8 if security_match else 0.5)

        # Access type confidence
        access_terms = ["entry", "exit", "door", "access", "elevator", "stair", "fire"]
        access_match = any(term in device_name for term in access_terms)
        confidence_factors.append(0.9 if access_match else 0.4)

        return sum(confidence_factors) / len(confidence_factors)

    def confirm_device_mapping(
        self, mappings: Dict[str, Dict], session_id: str
    ) -> bool:
        """Confirm device mappings (similar to column mapping confirmation)"""
        try:
            confirmed_data = {
                "confirmed_mappings": mappings,
                "status": "confirmed",
                "confirmed_at": "timestamp",
            }
            # Reuse existing storage method
            self.repository.store_entry_classification(session_id, confirmed_data)
            return True
        except Exception as exc:
            self.logger.error("device mapping confirmation failed: %s", exc)
            return False

    def get_device_mappings(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get device mappings for session"""
        return self.repository.get_entry_classification(session_id)
