from __future__ import annotations

"""Device learning feature callbacks."""

from dash import html
from dash._callback_context import callback_context
from dash.dependencies import Input, Output
import pandas as pd

from core.truly_unified_callbacks import TrulyUnifiedCallbacks
from yosai_intel_dashboard.src.services.interfaces import get_device_learning_service


def register_callbacks(app, container) -> None:
    """Register device learning callbacks."""
    callbacks = TrulyUnifiedCallbacks(app)

    @callbacks.register_handler(
        Output("device-learning-status", "children"),
        [
            Input("file-upload-store", "data"),
            Input("device-mappings-confirmed", "data"),
        ],
        prevent_initial_call=True,
        callback_id="device_learning",
        component_name="device_learning_service",
    )
    def handle_device_learning(upload_data, confirmed_mappings):
        """Handle learning using consolidated service."""
        ctx = callback_context

        if not ctx.triggered:
            return ""

        trigger_id = ctx.triggered[0]["prop_id"]

        learning_service = get_device_learning_service(container)

        if "file-upload-store" in trigger_id and upload_data:
            df = pd.DataFrame(upload_data["data"])
            filename = upload_data["filename"]

            if learning_service.apply_to_global_store(df, filename):
                return html.Div(
                    [
                        html.I(
                            className="fas fa-brain me-2", **{"aria-hidden": "true"}
                        ),
                        "Learned device mappings applied!",
                    ],
                    className="text-success",
                )

        elif "device-mappings-confirmed" in trigger_id and confirmed_mappings:
            df = pd.DataFrame(confirmed_mappings["original_data"])
            filename = confirmed_mappings["filename"]
            mappings = confirmed_mappings["mappings"]

            fingerprint = learning_service.save_complete_mapping(df, filename, mappings)

            return html.Div(
                [
                    html.I(className="fas fa-save me-2", **{"aria-hidden": "true"}),
                    f"Mappings saved! ID: {fingerprint[:8]}",
                ],
                className="text-success",
            )

        return ""

    return None
