"""Client-side validation helpers for file uploads."""

from __future__ import annotations

from typing import Any, Dict, List

import dash_bootstrap_components as dbc
from dash import html


class ClientSideValidator:
    """Utility for handling client-side upload validation results."""

    def build_error_alerts(self, results: List[Dict[str, Any]]) -> List[Any]:
        """Convert validation results from the browser into alert components."""
        alerts: List[Any] = []
        for res in results:
            if res.get("valid", False):
                continue
            issues = ", ".join(res.get("issues", [])) or "Failed validation"
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
