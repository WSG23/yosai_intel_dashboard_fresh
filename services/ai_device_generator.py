"""
AI-powered device attribute generation service.
Enhanced for real device naming patterns like F01A, F02B, etc.
"""

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import pandas as pd


@dataclass
class DeviceAttributes:
    """AI-generated device attributes."""

    device_id: str
    device_name: str
    floor_number: int
    security_level: int
    is_entry: bool
    is_exit: bool
    is_elevator: bool
    is_stairwell: bool
    is_fire_escape: bool
    is_restricted: bool  # ADD THIS LINE
    confidence: float
    ai_reasoning: str


class AIDeviceGenerator:
    """Enhanced AI device attribute generator for real-world device names."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Floor extraction patterns - UPDATED for F01A, F02B format
        self.floor_patterns = [
            # Pattern for formats like F01A, F02B, F03C
            (r"[Ff]0*(\d+)[A-Z]", lambda m: int(m.group(1))),  # F01A → 1, F02B → 2
            (
                r"[Ff](\d{2,3})[A-Z]",
                lambda m: (
                    int(m.group(1)[:1]) if len(m.group(1)) >= 2 else int(m.group(1))
                ),
            ),  # F10A → 1 (first digit)
            # Alternative patterns for your format
            (r"^[Ff]0*(\d+)", lambda m: int(m.group(1))),  # F01, F02, F03 at start
            (r"[Ff]0*(\d+)", lambda m: int(m.group(1))),  # F01, F02, F03 anywhere
            # Standard patterns
            (r"[Ll](\d+)", lambda m: int(m.group(1))),  # L1, l2
            (r"(\d+)[Ff]", lambda m: int(m.group(1))),  # 2F, 3f
            (r"[Ff]loor.*?(\d+)", lambda m: int(m.group(1))),  # floor_3
            (r"^(\d+)_", lambda m: int(m.group(1))),  # 1_door
        ]

        # Security level patterns - UPDATED for your device types
        self.security_patterns = [
            # High security areas
            (r"server|data center|data room", 9),
            (r"security.*(?:camera|room|office)", 8),
            (r"telecom.*room|network.*room|comms?.*room", 7),
            # Medium-high security
            (r"corner.*office|executive|admin", 6),
            (r"office(?:\s+|$)", 5),
            # Medium security - gates and access points
            (r"gate.*\d+.*(?:entry|exit)", 4),
            (r"gate.*\d+", 4),
            # Lower security - movement areas
            (r"staircase|stairs|stairwell", 3),
            (r"elevator|lift", 3),
            # Exits and emergency
            (r"exit|egress", 4),
            (r"entry|entrance", 4),
            (r"emergency|fire", 6),
        ]

        # Access type patterns - ENHANCED
        self.access_patterns = {
            "entry": [r"entry|entrance|in\b", r"gate.*entry"],
            "exit": [r"exit|egress|out\b", r"gate.*exit"],
            "elevator": [r"elevator|lift|elev"],
            "stairwell": [r"staircase|stairs|stairwell"],
            "fire_escape": [
                r"fire.*(?:exit|escape)|emergency.*(?:exit|escape)"
            ],  # FIXED: Complete pattern
            "restricted": [
                r"restricted|secure|authorized|private|limited"
            ],  # ADD THIS LINE
        }

        # Location-specific patterns for better naming
        self.location_patterns = {
            r"[Ff]0*(\d+)([A-Z])": r"Floor \1 Wing \2",  # F01A → Floor 1 Wing A
            r"gate\s*(\d+)": r"Gate \1",  # gate 5 → Gate 5
            r"server\s*(\d+)": r"Server \1",  # server 1 → Server 1
            r"staircase\s*([A-Z])": r"Staircase \1",  # staircase A → Staircase A
        }

    def generate_device_attributes(
        self, device_id: str, usage_data: Optional[pd.DataFrame] = None
    ) -> DeviceAttributes:
        """
        Generate comprehensive device attributes using enhanced AI analysis.

        Args:
            device_id: Device identifier to analyze
            usage_data: Optional usage patterns for enhanced analysis

        Returns:
            DeviceAttributes with AI-generated properties
        """
        device_lower = device_id.lower()
        reasoning_parts = []

        # Extract floor number with enhanced patterns
        floor_num = self._extract_floor(device_id, reasoning_parts)

        # Calculate security level with specific patterns
        security_level = self._calculate_security_level(device_lower, reasoning_parts)

        # Determine access types
        access_flags = self._determine_access_types(device_lower, reasoning_parts)

        # Generate enhanced readable name
        device_name = self._generate_enhanced_device_name(device_id, reasoning_parts)

        # Calculate confidence with better scoring
        confidence = self._calculate_enhanced_confidence(device_id, reasoning_parts)

        return DeviceAttributes(
            device_id=device_id,
            device_name=device_name,
            floor_number=floor_num,
            security_level=security_level,
            is_entry=access_flags["entry"],
            is_exit=access_flags["exit"] or access_flags["fire_escape"],
            is_elevator=access_flags["elevator"],
            is_stairwell=access_flags["stairwell"],
            is_fire_escape=access_flags["fire_escape"],
            is_restricted=access_flags["restricted"],  # ADD THIS LINE
            confidence=confidence,
            ai_reasoning="; ".join(reasoning_parts),
        )

    def _extract_floor(self, device_id: str, reasoning: List[str]) -> int:
        """Extract floor number using enhanced pattern matching."""
        for pattern, extractor in self.floor_patterns:
            match = re.search(pattern, device_id)
            if match:
                try:
                    floor = extractor(match)
                    if 1 <= floor <= 99:  # Reasonable floor range
                        reasoning.append(
                            f"Floor {floor} extracted from pattern '{pattern}'"
                        )
                        return floor
                except (ValueError, IndexError):
                    continue

        reasoning.append("Floor 1 (default - no pattern match)")
        return 1

    def _calculate_security_level(self, device_lower: str, reasoning: List[str]) -> int:
        """Calculate security level with enhanced pattern matching."""
        for pattern, level in self.security_patterns:
            if re.search(pattern, device_lower):
                reasoning.append(f"Security level {level} - matched '{pattern}'")
                return level

        reasoning.append("Security level 5 (default)")
        return 5

    def _determine_access_types(
        self, device_lower: str, reasoning: List[str]
    ) -> Dict[str, bool]:
        """Determine access type boolean flags with enhanced patterns."""
        flags = {access_type: False for access_type in self.access_patterns.keys()}

        for access_type, patterns in self.access_patterns.items():
            for pattern in patterns:
                if re.search(pattern, device_lower):
                    flags[access_type] = True
                    reasoning.append(f"Detected {access_type} from '{pattern}'")
                    break

        return flags

    def _generate_enhanced_device_name(
        self, device_id: str, reasoning: List[str]
    ) -> str:
        """Generate enhanced human-readable device name."""
        name = device_id

        # Apply location-specific transformations
        for pattern, replacement in self.location_patterns.items():
            if re.search(pattern, device_id):
                name = re.sub(pattern, replacement, device_id)
                break

        # If no specific transformation, clean up generically
        if name == device_id:
            # Replace underscores and hyphens with spaces
            name = re.sub(r"[_-]", " ", device_id)
            # Add spaces before numbers when appropriate
            name = re.sub(r"([a-zA-Z])([0-9])", r"\1 \2", name)
            # Capitalize words
            name = " ".join(word.capitalize() for word in name.split())

        reasoning.append(f"Generated readable name")
        return name

    def _calculate_enhanced_confidence(
        self, device_id: str, reasoning: List[str]
    ) -> float:
        """Calculate enhanced confidence score."""
        base_confidence = 0.5

        # Boost for successful pattern matches (not defaults)
        successful_patterns = len(
            [
                r
                for r in reasoning
                if "extracted" in r or "matched" in r or "detected" in r
            ]
        )
        default_patterns = len([r for r in reasoning if "default" in r])

        # Higher boost for pattern recognition
        confidence_boost = successful_patterns * 0.2
        confidence_penalty = default_patterns * 0.1

        # Extra boost for your specific F01A, F02B format
        if re.search(r"[Ff]0*\d+[A-Z]", device_id):
            confidence_boost += 0.15

        final_confidence = base_confidence + confidence_boost - confidence_penalty
        return min(max(final_confidence, 0.3), 0.95)


def create_ai_device_generator() -> AIDeviceGenerator:
    """Factory function for AI device generator."""
    return AIDeviceGenerator()
