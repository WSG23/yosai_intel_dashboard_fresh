"""Client-side validation helpers for file uploads."""

from __future__ import annotations

from typing import Any, Dict, List

import dash_bootstrap_components as dbc
from dash import html


class ClientSideValidator:
    """Utility for handling client-side upload validation results."""

    ISSUE_MESSAGES = {
        "too_large": "File exceeds size limit",
        "duplicate": "Duplicate file",
        "bad_magic": "File contents do not match type",
        "unsupported_type": "Unsupported file type",
        "decode_error": "Failed to decode data",
        "custom_error": "Custom validation failed",
    }

    def build_error_alerts(self, results: List[Dict[str, Any]]) -> List[Any]:
        """Convert validation results from the browser into alert components."""
        alerts: List[Any] = []
        for res in results:
            if res.get("valid", False):
                continue
            raw = res.get("issues", [])
            issues = ", ".join(
                self.ISSUE_MESSAGES.get(code, str(code)) for code in raw
            ) or "Failed validation"
            alerts.append(
                dbc.Alert(
                    [html.Strong(res.get("filename", "Unknown")), f": {issues}"],
                    color="danger",
                    dismissable=True,
                    className="mb-2",
                )
            )
        return alerts


__all__ = ["ClientSideValidator"]
