import logging
from typing import Dict

import pandas as pd

from services.device_learning_service import get_device_learning_service

logger = logging.getLogger(__name__)


def analyze_device_name_with_ai(device_name: str) -> Dict[str, any]:
    """Return AI-generated device info unless a user mapping exists."""
    try:
        from services.ai_mapping_store import ai_mapping_store

        mapping = ai_mapping_store.get(device_name)
        if mapping and mapping.get("source") == "user_confirmed":
            logger.info(f"\U0001f512 Using USER CONFIRMED mapping for '{device_name}'")
            return mapping

        logger.info(f"\U0001f916 No user mapping found, generating AI analysis for '{device_name}'")
        from services.ai_device_generator import AIDeviceGenerator

        ai_generator = AIDeviceGenerator()
        result = ai_generator.generate_device_attributes(device_name)
        return {
            "floor_number": result.floor_number,
            "security_level": result.security_level,
            "confidence": result.confidence,
            "is_entry": result.is_entry,
            "is_exit": result.is_exit,
            "device_name": result.device_name,
            "ai_reasoning": result.ai_reasoning,
            "source": "ai_generated",
        }
    except Exception as e:  # pragma: no cover - fallback behaviour
        logger.info(f"\u274c Error in device analysis: {e}")
        return {
            "floor_number": 1,
            "security_level": 5,
            "confidence": 0.1,
            "source": "fallback",
        }


def auto_apply_learned_mappings(df: pd.DataFrame, filename: str) -> bool:
    """Auto-apply any learned mappings for this file type."""
    try:
        learning_service = get_device_learning_service()
        learned_mappings = learning_service.get_learned_mappings(df, filename)
        if learned_mappings:
            learning_service.apply_learned_mappings_to_global_store(df, filename)
            logger.info(f"🤖 Auto-applied {len(learned_mappings)} learned device mappings")
            return True
        return False
    except Exception as e:  # pragma: no cover - best effort
        logger.error(f"Failed to auto-apply learned mappings: {e}")
        return False


__all__ = ["analyze_device_name_with_ai", "auto_apply_learned_mappings"]
