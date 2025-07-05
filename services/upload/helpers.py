import json
import logging
from datetime import datetime
from typing import Dict

from dash._callback_context import callback_context

logger = logging.getLogger(__name__)


def get_trigger_id() -> str:
    """Return the triggered Dash callback identifier."""
    ctx = callback_context
    return ctx.triggered[0]["prop_id"] if ctx.triggered else ""


def save_ai_training_data(filename: str, mappings: Dict[str, str], file_info: Dict):
    """Save confirmed mappings for AI training."""
    try:
        logger.info("🤖 Saving AI training data for %s", filename)
        training_data = {
            "filename": filename,
            "timestamp": datetime.now().isoformat(),
            "mappings": mappings,
            "reverse_mappings": {v: k for k, v in mappings.items()},
            "column_count": len(file_info.get("columns", [])),
            "ai_suggestions": file_info.get("ai_suggestions", {}),
            "user_verified": True,
        }

        from components.plugin_adapter import ComponentPluginAdapter

        if ComponentPluginAdapter().save_verified_mappings(filename, mappings, {}):
            logger.info("✅ AI training data saved via plugin")
        else:
            logger.info("⚠️ AI training save failed")

        import os

        os.makedirs("data/training", exist_ok=True)
        with open(
            f"data/training/mappings_{datetime.now().strftime('%Y%m%d')}.jsonl",
            "a",
            encoding="utf-8",
            errors="replace",
        ) as f:
            f.write(json.dumps(training_data) + "\n")

        logger.info("✅ Training data saved locally")
    except Exception as e:  # pragma: no cover - best effort
        logger.info("❌ Error saving training data: %s", e)


__all__ = ["get_trigger_id", "save_ai_training_data"]
