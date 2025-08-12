import logging
from typing import Any, Dict, List

from dash.dash import no_update

from yosai_intel_dashboard.src.core import registry

logger = logging.getLogger(__name__)


class AISuggestionService:
    """Service for AI-driven helpers used in the upload page."""

    def analyze_device_name_with_ai(self, device_name: str) -> Dict[str, Any]:
        try:
            from yosai_intel_dashboard.src.services.ai_mapping_store import ai_mapping_store

            # Check for any cached mapping first
            mapping = ai_mapping_store.get(device_name)
            if mapping:
                src = mapping.get("source", "cached")
                if src == "user_confirmed":
                    logger.info("🔐 Using USER CONFIRMED mapping for '%s'", device_name)
                else:
                    logger.info("📦 Using cached mapping for '%s'", device_name)
                return mapping

            logger.info("🤖 Generating AI analysis for '%s'", device_name)
            from yosai_intel_dashboard.src.services.ai_device_generator import AIDeviceGenerator

            ai_generator = AIDeviceGenerator()
            result = ai_generator.generate_device_attributes(device_name)
            mapping = {
                "floor_number": result.floor_number,
                "security_level": result.security_level,
                "confidence": result.confidence,
                "is_entry": result.is_entry,
                "is_exit": result.is_exit,
                "device_name": result.device_name,
                "ai_reasoning": result.ai_reasoning,
                "source": "ai_generated",
            }
            # Cache the result for future calls
            ai_mapping_store.set(device_name, mapping)
            return mapping
        except Exception as exc:
            logger.info("❌ Error in device analysis: %s", exc)
            return {
                "floor_number": 1,
                "security_level": 5,
                "confidence": 0.1,
                "source": "fallback",
            }

    def apply_ai_suggestions(self, n_clicks: int | None, file_info: Dict[str, Any]):
        if not n_clicks or not file_info:
            return [no_update]

        ai_suggestions = file_info.get("ai_suggestions", {})
        columns: List[str] = file_info.get("columns", [])

        logger.info("🤖 Applying AI suggestions for %s columns", len(columns))
        suggested_values: List[Any] = []
        for column in columns:
            suggestion = ai_suggestions.get(column, {})
            confidence = suggestion.get("confidence", 0.0)
            field = suggestion.get("field", "")
            if confidence > 0.3 and field:
                suggested_values.append(field)
                logger.info("   ✅ %s -> %s (%.0f%%)", column, field, confidence * 100)
            else:
                suggested_values.append(None)
                logger.info(
                    "   ❓ %s -> No confident suggestion (%.0f%%)",
                    column,
                    confidence * 100,
                )
        return [suggested_values]


# Register service for global lookups
registry.register("ai_suggestion_service", AISuggestionService())


def analyze_device_name_with_ai(device_name: str) -> Dict[str, Any]:
    """Convenience wrapper calling :class:`AISuggestionService`."""
    service: AISuggestionService = registry.get("ai_suggestion_service")
    return service.analyze_device_name_with_ai(device_name)


__all__ = ["AISuggestionService", "analyze_device_name_with_ai"]
