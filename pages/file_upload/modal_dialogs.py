from typing import Any, Tuple, List
import logging

from dash import html, dcc, no_update
import dash_bootstrap_components as dbc

logger = logging.getLogger(__name__)


def handle_modal_dialogs(trigger_id: str, verify_clicks: int | None, classify_clicks: int | None, confirm_clicks: int | None, cancel_col_clicks: int | None, cancel_dev_clicks: int | None) -> Tuple[Any, Any, Any]:
    """Open or close the column/device verification modals."""
    if "verify-columns-btn-simple" in trigger_id and verify_clicks:
        return no_update, True, no_update
    if "classify-devices-btn" in trigger_id and classify_clicks:
        return no_update, no_update, True
    if "column-verify-confirm" in trigger_id and confirm_clicks:
        return no_update, False, no_update
    if "column-verify-cancel" in trigger_id or "device-verify-cancel" in trigger_id:
        return no_update, False, False
    return no_update, no_update, no_update


def apply_ai_suggestions(n_clicks: int | None, file_info: dict) -> List[Any]:
    """Return suggested column mappings from AI results."""
    if not n_clicks or not file_info:
        return [no_update]
    ai_suggestions = file_info.get("ai_suggestions", {})
    columns = file_info.get("columns", [])
    suggested_values = []
    for column in columns:
        suggestion = ai_suggestions.get(column, {})
        confidence = suggestion.get("confidence", 0.0)
        field = suggestion.get("field", "")
        if confidence > 0.3 and field:
            suggested_values.append(field)
        else:
            suggested_values.append(None)
    return [suggested_values]


__all__ = ["handle_modal_dialogs", "apply_ai_suggestions"]

