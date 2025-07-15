"""Dash callback handlers for the deep analytics page."""

from typing import TYPE_CHECKING, Any

from dash import Input, Output, State, callback_context, html
from dash.exceptions import PreventUpdate

if TYPE_CHECKING:
    from core.truly_unified_callbacks import TrulyUnifiedCallbacks

import logging

from analytics.controllers import (
    UnifiedAnalyticsController,
    dispatch_analysis,
    get_data_sources,
    get_initial_message_safe,
    run_quality_analysis,
    run_service_analysis,
    run_suggests_analysis,
    run_unique_patterns_analysis,
)
from analytics.controllers import update_status_alert as _controller_update_status_alert
from core.callback_registry import _callback_registry
from core.dash_profile import profile_callback
from core.state import CentralizedStateManager

logger = logging.getLogger(__name__)
import dash_bootstrap_components as dbc

analytics_state = CentralizedStateManager()


# ------------------------------------------------------------
# Callback manager
# ------------------------------------------------------------


class Callbacks:
    """Container for deep analytics callbacks."""

    def handle_analysis_buttons(
        self,
        security_n,
        trends_n,
        behavior_n,
        anomaly_n,
        suggests_n,
        quality_n,
        unique_n,
        data_source,
    ):
        """Handle analysis button clicks and dispatch to helper functions."""

        if not callback_context.triggered:
            return get_initial_message_safe()

        if not data_source or data_source == "none":
            return dbc.Alert("Please select a data source first", color="warning")

        button_id = callback_context.triggered[0]["prop_id"].split(".")[0]

        try:
            return dispatch_analysis(button_id, data_source)
        except Exception as e:  # pragma: no cover - catch unforeseen errors
            return dbc.Alert(f"Analysis failed: {str(e)}", color="danger")

    def handle_refresh_data_sources(self, n_clicks):
        """Refresh data sources when button clicked."""
        if not callback_context.triggered:
            raise PreventUpdate

        return get_data_sources()

    def update_status_alert(self, trigger):
        """Update status based on service health."""
        return _controller_update_status_alert(trigger)


# =============================================================================
# SECTION 7: HELPER DISPLAY FUNCTIONS
# Add these helper functions for non-suggests analysis types
# =============================================================================


def register_callbacks(
    manager: "TrulyUnifiedCallbacks",
    controller: UnifiedAnalyticsController | None = None,
) -> None:
    """Instantiate :class:`Callbacks` and register its methods."""

    def _do_registration() -> None:
        cb = Callbacks()

        manager.register_operation(
            "analysis_buttons",
            lambda s, t, b, a, sug, q, u, ds: cb.handle_analysis_buttons(
                s, t, b, a, sug, q, u, ds
            ),
            name="handle_analysis_buttons",
            timeout=5,
        )
        manager.register_operation(
            "refresh_sources",
            lambda n: cb.handle_refresh_data_sources(n),
            name="refresh_data_sources",
        )
        manager.register_operation(
            "status_alert",
            lambda val: cb.update_status_alert(val),
            name="update_status_alert",
        )

        @manager.register_handler(
            [
                Output("analytics-display-area", "children"),
                Output("analytics-data-source", "options"),
                Output("status-alert", "children"),
            ],
            [
                Input("security-btn", "n_clicks"),
                Input("trends-btn", "n_clicks"),
                Input("behavior-btn", "n_clicks"),
                Input("anomaly-btn", "n_clicks"),
                Input("suggests-btn", "n_clicks"),
                Input("quality-btn", "n_clicks"),
                Input("unique-patterns-btn", "n_clicks"),
                Input("refresh-sources-btn", "n_clicks"),
                Input("hidden-trigger", "children"),
            ],
            [State("analytics-data-source", "value")],
            callback_id="deep_analytics_operations",
            component_name="deep_analytics",
            prevent_initial_call=True,
        )
        def analytics_operations(
            sec, trn, beh, anom, sug, qual, uniq, refresh, trigger, data_source
        ):
            display = manager.execute_group(
                "analysis_buttons",
                sec,
                trn,
                beh,
                anom,
                sug,
                qual,
                uniq,
                data_source,
            )[0]

            options = manager.execute_group("refresh_sources", refresh)[0]

            alert = manager.execute_group("status_alert", trigger)[0]

            analytics_state.dispatch(
                "UPDATE", {"display": display, "options": options, "alert": alert}
            )

            return display, options, alert

        if controller is not None:
            controller.register_handler(
                "on_analysis_error",
                lambda aid, err: logger.error("Deep analytics error: %s", err),
            )

    _callback_registry.register_deduplicated(
        ["deep_analytics_operations"], _do_registration, source_module="deep_analytics"
    )


__all__ = ["Callbacks", "register_callbacks"]


def __getattr__(name: str):
    if name.startswith(("create_", "get_")):

        def _stub(*args, **kwargs):
            return None

        return _stub
    raise AttributeError(f"module {__name__} has no attribute {name}")
