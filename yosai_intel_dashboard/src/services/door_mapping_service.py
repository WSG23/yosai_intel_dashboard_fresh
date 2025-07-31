"""
Door Mapping Service - Business logic for device attribute assignment
Handles AI model data processing and manual override management
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from core.protocols import ConfigurationServiceProtocol

# ADD after existing imports
from yosai_intel_dashboard.src.services.ai_device_generator import AIDeviceGenerator
from yosai_intel_dashboard.src.services.common import ModelRegistry
from yosai_intel_dashboard.src.services.common.config_utils import common_init, create_config_methods
from yosai_intel_dashboard.src.services.configuration_service import DynamicConfigurationService
from yosai_intel_dashboard.src.services.learning.src.api.consolidated_service import get_learning_service

logger = logging.getLogger(__name__)


@dataclass
class DeviceAttributeData:
    """Device attribute data structure"""

    door_id: str
    name: str
    is_entry: bool = False
    is_exit: bool = False
    is_elevator: bool = False
    is_stairwell: bool = False
    is_fire_escape: bool = False
    is_restricted: bool = False
    other: bool = False
    security_level: int = 50
    confidence: Optional[int] = None
    ai_generated: bool = True
    manually_edited: bool = False
    edit_timestamp: Optional[datetime] = None


@create_config_methods
class DoorMappingService:
    """Service for handling door mapping and device attribute assignment"""

    def __init__(
        self,
        config: ConfigurationServiceProtocol,
        *,
        model_registry: ModelRegistry | None = None,
        fallback_version: str = "v1",
    ) -> None:
        common_init(self, config)
        self._registry = model_registry or ModelRegistry()
        self.fallback_version = fallback_version
        self.ai_model_version = fallback_version
        self.confidence_threshold = config.get_ai_confidence_threshold()

    def process_uploaded_data(
        self, df: pd.DataFrame, client_profile: str = "auto"
    ) -> Dict[str, Any]:
        """
        Process uploaded CSV/JSON/Excel data and generate device attribute assignments

        Args:
            df: Uploaded data as pandas DataFrame
            client_profile: Client configuration profile

        Returns:
            Dict containing processed device data and metadata
        """
        try:
            version = self._registry.get_active_version(
                "door-mapping", self.fallback_version
            )
            self.ai_model_version = version or self.fallback_version
            # Validate required columns
            required_columns = ["door_id"]
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")

            # Extract unique devices
            unique_doors = df["door_id"].unique()

            # Generate AI attribute assignments
            devices_data = []
            for door_id in unique_doors:
                device_data = self._generate_ai_attributes(door_id, df, client_profile)
                devices_data.append(device_data)

            # Prepare response
            response = {
                "devices": [device.__dict__ for device in devices_data],
                "metadata": {
                    "total_devices": len(devices_data),
                    "ai_model_version": self.ai_model_version,
                    "client_profile": client_profile,
                    "processing_timestamp": datetime.now().isoformat(),
                    "confidence_threshold": self.confidence_threshold,
                },
            }

            logger.info(f"Processed {len(devices_data)} devices for door mapping")
            return response

        except Exception as e:
            logger.error(f"Error processing uploaded data: {e}")
            raise

    def _generate_ai_attributes(
        self, door_id: str, df: pd.DataFrame, client_profile: str
    ) -> DeviceAttributeData:
        """Generate AI-based attribute assignments.

        Uses an enhanced modular AI generator.
        """

        # Use new modular AI generator
        ai_generator = AIDeviceGenerator()
        device_rows = df[df["door_id"] == door_id]

        # Generate attributes using enhanced AI
        ai_attributes = ai_generator.generate_device_attributes(door_id, device_rows)

        # Apply client profile adjustments
        security_level = ai_attributes.security_level
        if client_profile == "high_security":
            security_level = min(100, security_level + 20)
        elif client_profile == "low_security":
            security_level = max(0, security_level - 20)

        # Convert confidence from 0.0-1.0 scale to 0-100 scale
        confidence_percentage = int(ai_attributes.confidence * 100)

        # Convert to DeviceAttributeData with standardized keys
        return DeviceAttributeData(
            door_id=ai_attributes.device_id,
            name=ai_attributes.device_name,
            is_entry=ai_attributes.is_entry,
            is_exit=ai_attributes.is_exit,
            is_elevator=ai_attributes.is_elevator,
            is_stairwell=ai_attributes.is_stairwell,
            is_fire_escape=ai_attributes.is_fire_escape,
            is_restricted=ai_attributes.is_restricted,
            other=not any(
                [
                    ai_attributes.is_entry,
                    ai_attributes.is_exit,
                    ai_attributes.is_elevator,
                    ai_attributes.is_stairwell,
                    ai_attributes.is_fire_escape,
                    ai_attributes.is_restricted,  # ADD THIS LINE
                ]
            ),
            security_level=security_level,
            confidence=confidence_percentage,
            ai_generated=True,
            manually_edited=False,
        )

    def _generate_device_name(self, door_id: str, device_rows: pd.DataFrame) -> str:
        """Generate a human-readable device name"""
        # Clean up door_id and make it more readable
        name = door_id.replace("_", " ").replace("-", " ")

        # Capitalize words
        name = " ".join(word.capitalize() for word in name.split())

        # Add context if available from data
        if len(device_rows) > 0:
            # Check for common patterns in access data
            if any("entry" in str(device_rows.iloc[0]).lower() for _ in [True]):
                pass  # Keep name as is

        return name

    def _analyze_door_patterns(
        self, door_id: str, device_rows: pd.DataFrame, client_profile: str
    ) -> Dict[str, Any]:
        """
        Analyze door ID patterns to determine likely attributes

        This is where the AI model logic would go. For now, using rule-based patterns.
        """
        door_id_lower = door_id.lower()
        attributes = {
            "entry": False,
            "exit": False,
            "elevator": False,
            "stairwell": False,
            "fire_escape": False,
            "other": False,
            "security_level": 50,
        }

        # Pattern matching for door types
        if any(
            keyword in door_id_lower
            for keyword in ["entry", "entrance", "front", "main"]
        ):
            attributes["entry"] = True
            attributes["security_level"] = 70

        if any(
            keyword in door_id_lower
            for keyword in ["exit", "back", "rear", "emergency"]
        ):
            attributes["exit"] = True
            attributes["security_level"] = 60

        if any(keyword in door_id_lower for keyword in ["elevator", "lift", "elev"]):
            attributes["elevator"] = True
            attributes["security_level"] = 40

        if any(
            keyword in door_id_lower for keyword in ["stair", "stairwell", "stairs"]
        ):
            attributes["stairwell"] = True
            attributes["security_level"] = 55

        if any(keyword in door_id_lower for keyword in ["fire", "emergency", "escape"]):
            attributes["fire_escape"] = True
            attributes["security_level"] = 80

        # If no specific pattern matched, mark as other
        if not any(
            attributes[key]
            for key in ["entry", "exit", "elevator", "stairwell", "fire_escape"]
        ):
            attributes["other"] = True

        # Adjust security levels based on client profile
        if client_profile == "high_security":
            attributes["security_level"] = min(100, attributes["security_level"] + 20)
        elif client_profile == "low_security":
            attributes["security_level"] = max(0, attributes["security_level"] - 20)

        return attributes

    def _calculate_confidence_score(
        self, door_id: str, attributes: Dict[str, Any], device_rows: pd.DataFrame
    ) -> int:
        """Calculate confidence score for AI-generated attributes"""
        confidence = 50  # Base confidence

        # Increase confidence for clear patterns
        door_id_lower = door_id.lower()
        clear_patterns = ["entry", "exit", "elevator", "stair", "fire", "emergency"]

        for pattern in clear_patterns:
            if pattern in door_id_lower:
                confidence += 15

        # Increase confidence based on data volume
        if len(device_rows) > 100:
            confidence += 10
        elif len(device_rows) > 50:
            confidence += 5

        # Cap at 95% (never 100% to indicate AI uncertainty)
        return min(95, confidence)

    def apply_manual_edits(
        self, original_data: List[Dict], manual_edits: Dict[str, Dict]
    ) -> List[Dict]:
        """
        Apply manual edits to device data

        Args:
            original_data: Original AI-generated device data
            manual_edits: Manual edits per device

        Returns:
            Updated device data with manual edits applied
        """
        updated_data = []

        for device in original_data:
            device_id = device["door_id"]

            # Create a copy of the device data
            updated_device = device.copy()

            # Apply manual edits if they exist
            if device_id in manual_edits:
                edits = manual_edits[device_id]

                # Update attributes
                for attr, value in edits.items():
                    if attr in updated_device:
                        updated_device[attr] = value

                # Mark as manually edited
                updated_device["manually_edited"] = True
                updated_device["edit_timestamp"] = datetime.now().isoformat()
                updated_device["confidence"] = (
                    None  # Clear AI confidence for manual edits
                )

            updated_data.append(updated_device)

        return updated_data

    def save_verified_mapping(self, mapping_data: Dict[str, Any], user_id: str) -> bool:
        """
        Save verified column mapping for future use

        Args:
            mapping_data: Verified mapping configuration
            user_id: User identifier

        Returns:
            Success status
        """
        try:
            mapping_record = {
                "user_id": user_id,
                "timestamp_col": mapping_data.get("timestamp"),
                "device_col": mapping_data.get("device_name"),
                "user_col": mapping_data.get("token_id"),
                "event_type_col": mapping_data.get("event_type"),
                "floor_estimate": mapping_data.get("floors", 1),
                "verified_at": datetime.now().isoformat(),
                "ai_model_version": self.ai_model_version,
            }

            # Store in your preferred storage system
            # This could be database, file, or cache depending on your setup
            logger.info(f"Saved verified mapping for user {user_id}: {mapping_record}")

            return True

        except Exception as e:
            logger.error(f"Error saving verified mapping: {e}")
            return False

    def save_manual_edits_for_training(
        self, manual_edits: Dict[str, Dict], original_data: List[Dict]
    ):
        """
        Save manual edits to improve AI model training

        This would typically save to a training database for model improvement
        """
        try:
            training_data = {
                "timestamp": datetime.now().isoformat(),
                "ai_model_version": self.ai_model_version,
                "manual_edits": manual_edits,
                "original_ai_predictions": original_data,
                "edit_count": len(manual_edits),
            }

            # Here you would save to your training database
            # For now, just log the information
            logger.info(f"Saved {len(manual_edits)} manual edits for AI training")

            return training_data

        except Exception as e:
            logger.error(f"Error saving manual edits for training: {e}")
            raise

    def apply_learned_mappings(self, df: pd.DataFrame, filename: str) -> bool:
        """Apply previously learned device mappings if available"""
        try:
            learning_service = get_learning_service()
            return learning_service.apply_to_global_store(df, filename)
        except Exception as e:
            logger.error(f"Error applying learned mappings: {e}")
            return False

    def debug_device_names(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Debug function to see actual device names and AI analysis"""
        if "door_id" not in df.columns:
            return {"error": "No door_id column found"}

        device_names = df["door_id"].unique()[:10]
        debug_info = {
            "total_devices": len(df["door_id"].unique()),
            "sample_device_names": device_names.tolist(),
            "ai_analysis": {},
        }

        ai_generator = AIDeviceGenerator()
        for device_name in device_names:
            try:
                ai_attrs = ai_generator.generate_device_attributes(str(device_name))
                debug_info["ai_analysis"][device_name] = {
                    "generated_name": ai_attrs.device_name,
                    "floor": ai_attrs.floor_number,
                    "security_level": ai_attrs.security_level,
                    "confidence": ai_attrs.confidence,
                    "reasoning": ai_attrs.ai_reasoning,
                    "access_types": {
                        "is_entry": ai_attrs.is_entry,
                        "is_exit": ai_attrs.is_exit,
                        "is_elevator": ai_attrs.is_elevator,
                    },
                }
            except Exception as e:
                debug_info["ai_analysis"][device_name] = {"error": str(e)}

        return debug_info

    def save_confirmed_mappings(
        self,
        df: pd.DataFrame,
        filename: str,
        confirmed_devices: List[Dict[str, Any]],
    ) -> str:
        """Save confirmed device mappings for future learning"""
        try:
            device_mappings = {}
            for device in confirmed_devices:
                device_id = device.get("door_id", device.get("device_id"))
                if device_id:
                    device_mappings[device_id] = {
                        "device_name": device.get("name", ""),
                        "floor_number": device.get("floor_number", 1),
                        "security_level": device.get("security_level", 50),
                        "is_entry": device.get("is_entry", device.get("entry", False)),
                        "is_exit": device.get("is_exit", device.get("exit", False)),
                        "is_elevator": device.get(
                            "is_elevator", device.get("elevator", False)
                        ),
                        "is_stairwell": device.get(
                            "is_stairwell", device.get("stairwell", False)
                        ),
                        "is_fire_escape": device.get(
                            "is_fire_escape", device.get("fire_escape", False)
                        ),
                        "is_restricted": device.get(
                            "is_restricted", device.get("restricted", False)
                        ),
                    }

            learning_service = get_learning_service()
            fingerprint = learning_service.save_complete_mapping(
                df, filename, device_mappings
            )

            logger.info(
                "Saved %d device mappings with ID: %s",
                len(device_mappings),
                fingerprint[:8],
            )
            return fingerprint

        except Exception as e:
            logger.error(f"Error saving confirmed mappings: {e}")
            return ""


# Service instance
door_mapping_service = DoorMappingService(DynamicConfigurationService())

__all__ = ["DoorMappingService", "DeviceAttributeData", "door_mapping_service"]
