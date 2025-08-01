import logging
from typing import Any, Dict, Sequence

from yosai_intel_dashboard.src.services.data_enhancer.mapping_utils import get_ai_column_suggestions

logger = logging.getLogger(__name__)


def generate_column_suggestions(columns: Sequence[str]) -> Dict[str, Dict[str, Any]]:
    """Return AI-based column suggestions for the given column names."""
    try:
        return get_ai_column_suggestions(columns)
    except Exception as exc:  # pragma: no cover - best effort
        logger.exception("Fallback column suggestion logic failed: %s", exc)
        return {c: {"field": "", "confidence": 0.0} for c in columns}


__all__ = ["generate_column_suggestions"]
