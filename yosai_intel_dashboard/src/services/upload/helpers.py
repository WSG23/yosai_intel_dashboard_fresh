from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict

import aiofiles

logger = logging.getLogger(__name__)


def get_trigger_id() -> str:
    """Return the triggered Dash callback identifier."""
    from dash import callback_context

    ctx = callback_context
    return ctx.triggered[0]["prop_id"] if ctx.triggered else ""


async def save_ai_training_data_async(
    filename: str, mappings: Dict[str, str], file_info: Dict
) -> None:
    """Asynchronously save confirmed mappings for AI training."""
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

        from yosai_intel_dashboard.src.components.plugin_adapter import (
            ComponentPluginAdapter,
        )

        # Run potentially blocking plugin operations in a thread
        try:
            saved = await asyncio.to_thread(
                ComponentPluginAdapter().save_verified_mappings,
                filename,
                mappings,
                {},
            )
            if saved:
                logger.info("✅ AI training data saved via plugin")
            else:
                logger.info("⚠️ AI training save failed")
        except Exception:
            logger.info("⚠️ AI training save failed")

        await asyncio.to_thread(os.makedirs, "data/training", True)
        file_name = f"data/training/mappings_{datetime.now().strftime('%Y%m%d')}.jsonl"
        async with aiofiles.open(
            file_name, "a", encoding="utf-8", errors="replace"
        ) as f:
            await f.write(json.dumps(training_data) + "\n")

        logger.info("✅ Training data saved locally")
    except Exception as e:  # pragma: no cover - best effort
        logger.info("❌ Error saving training data: %s", e)


def save_ai_training_data(
    filename: str, mappings: Dict[str, str], file_info: Dict
) -> None:
    """Synchronous wrapper around :func:`save_ai_training_data_async`."""
    asyncio.run(save_ai_training_data_async(filename, mappings, file_info))


__all__ = ["get_trigger_id", "save_ai_training_data", "save_ai_training_data_async"]
