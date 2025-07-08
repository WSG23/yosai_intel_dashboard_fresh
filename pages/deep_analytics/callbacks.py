"""Dash callback handlers for the deep analytics page."""

from typing import TYPE_CHECKING

from dash import Input, Output, State, callback_context, html
from dash.exceptions import PreventUpdate

if TYPE_CHECKING:
    from core.truly_unified_callbacks import TrulyUnifiedCallbacks

import logging

from analytics.controllers import UnifiedAnalyticsController
from core.dash_profile import profile_callback
from core.truly_unified_callbacks import TrulyUnifiedCallbacks
from core.state import CentralizedStateManager

logger = logging.getLogger(__name__)
import dash_bootstrap_components as dbc

callback_manager = TrulyUnifiedCallbacks()
analytics_state = CentralizedStateManager()

from services.data_processing.analytics_engine import (
    AI_SUGGESTIONS_AVAILABLE,
    analyze_data_with_service,
    get_analytics_service_safe,
    get_data_source_options_safe,
    process_quality_analysis_safe,
    process_suggests_analysis_safe,
)

from .analysis import (
    create_analysis_results_display,
    create_analysis_results_display_safe,
    get_initial_message_safe,
)


def run_suggests_analysis(data_source: str):
    """Return display component for suggests analysis."""
    results = process_suggests_analysis_safe(data_source)
    if isinstance(results, dict) and "error" in results:
        return dbc.Alert(str(results["error"]), color="danger")
    return create_analysis_results_display_safe(results, "suggests")


def run_quality_analysis(data_source: str):
    """Return display component for data quality analysis."""
    results = process_quality_analysis_safe(data_source)
    if isinstance(results, dict) and "error" in results:
        return dbc.Alert(str(results["error"]), color="danger")
    return create_analysis_results_display_safe(results, "quality")


def run_service_analysis(data_source: str, analysis_type: str):
    """Return display for service based analyses (security, trends, etc.)."""
    results = analyze_data_with_service(data_source, analysis_type)
    if isinstance(results, dict) and "error" in results:
        return dbc.Alert(str(results["error"]), color="danger")
    return create_analysis_results_display(results, analysis_type)


def run_unique_patterns_analysis(data_source: str):
    """Run unique patterns analysis using the analytics service."""
    try:
        analytics_service = get_analytics_service_safe()
        if not analytics_service:
            return dbc.Alert("Analytics service not available", color="danger")
        results = analytics_service.get_unique_patterns_analysis(data_source)

        if results["status"] == "success":
            data_summary = results["data_summary"]
            user_patterns = results["user_patterns"]
            device_patterns = results["device_patterns"]
            interaction_patterns = results["interaction_patterns"]
            temporal_patterns = results["temporal_patterns"]
            access_patterns = results["access_patterns"]
            recommendations = results["recommendations"]

            return html.Div(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.Card(
                                    dbc.CardBody(
                                        [
                                            html.H4(
                                                "Database Overview",
                                                className="card-title",
                                            ),
                                            html.H2(
                                                f"{data_summary['total_records']:,}",
                                                className="text-primary",
                                            ),
                                            html.P("Total Access Events"),
                                            html.Small(
                                                f"Spanning {data_summary['date_range']['span_days']} days"
                                            ),
                                        ]
                                    ),
                                    color="light",
                                ),
                                width=3,
                            ),
                            dbc.Col(
                                dbc.Card(
                                    dbc.CardBody(
                                        [
                                            html.H4(
                                                "Unique Users",
                                                className="card-title",
                                            ),
                                            html.H2(
                                                f"{data_summary['unique_entities']['users']:,}",
                                                className="text-success",
                                            ),
                                            html.P("Individual Users"),
                                            html.Small(
                                                f"Avg: {user_patterns.get('user_statistics', {}).get('mean_events_per_user', 0):.1f} events/user"
                                            ),
                                        ]
                                    ),
                                    color="light",
                                ),
                                width=3,
                            ),
                            dbc.Col(
                                dbc.Card(
                                    dbc.CardBody(
                                        [
                                            html.H4(
                                                "Unique Devices",
                                                className="card-title",
                                            ),
                                            html.H2(
                                                f"{data_summary['unique_entities']['devices']:,}",
                                                className="text-info",
                                            ),
                                            html.P("Access Points"),
                                            html.Small(
                                                f"Avg: {device_patterns.get('device_statistics', {}).get('mean_events_per_device', 0):.1f} events/device"
                                            ),
                                        ]
                                    ),
                                    color="light",
                                ),
                                width=3,
                            ),
                            dbc.Col(
                                dbc.Card(
                                    dbc.CardBody(
                                        [
                                            html.H4(
                                                "Interactions",
                                                className="card-title",
                                            ),
                                            html.H2(
                                                f"{interaction_patterns.get('total_unique_interactions', 0):,}",
                                                className="text-warning",
                                            ),
                                            html.P("User-Device Pairs"),
                                            html.Small(
                                                f"Success: {access_patterns.get('overall_success_rate', 0):.1%}"
                                            ),
                                        ]
                                    ),
                                    color="light",
                                ),
                                width=3,
                            ),
                        ]
                    ),
                    html.Hr(),
                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.Card(
                                    [
                                        dbc.CardHeader(
                                            html.H4("User Pattern Analysis")
                                        ),
                                        dbc.CardBody(
                                            html.Div(
                                                dbc.Row(
                                                    [
                                                        dbc.Col(
                                                            [
                                                                html.H5(
                                                                    "User Classifications"
                                                                ),
                                                                html.P(
                                                                    f"Power Users: {len(user_patterns.get('user_classifications', {}).get('power_users', []))}"
                                                                ),
                                                                html.P(
                                                                    f"Regular Users: {len(user_patterns.get('user_classifications', {}).get('regular_users', []))}"
                                                                ),
                                                                html.P(
                                                                    f"Occasional Users: {len(user_patterns.get('user_classifications', {}).get('occasional_users', []))}"
                                                                ),
                                                            ],
                                                            width=6,
                                                        ),
                                                        dbc.Col(
                                                            [
                                                                html.H5(
                                                                    "Access Patterns"
                                                                ),
                                                                html.P(
                                                                    f"Single-Door Users: {len(user_patterns.get('user_classifications', {}).get('single_door_users', []))}"
                                                                ),
                                                                html.P(
                                                                    f"Multi-Door Users: {len(user_patterns.get('user_classifications', {}).get('multi_door_users', []))}"
                                                                ),
                                                                html.P(
                                                                    f"Problematic Users: {len(user_patterns.get('user_classifications', {}).get('problematic_users', []))}"
                                                                ),
                                                            ],
                                                            width=6,
                                                        ),
                                                    ]
                                                )
                                            )
                                        ),
                                    ]
                                ),
                                width=6,
                            ),
                            dbc.Col(
                                dbc.Card(
                                    [
                                        dbc.CardHeader(
                                            html.H4("Device Pattern Analysis")
                                        ),
                                        dbc.CardBody(
                                            html.Div(
                                                dbc.Row(
                                                    [
                                                        dbc.Col(
                                                            [
                                                                html.H5(
                                                                    "Traffic Classifications"
                                                                ),
                                                                html.P(
                                                                    f"High Traffic: {len(device_patterns.get('device_classifications', {}).get('high_traffic_devices', []))}"
                                                                ),
                                                                html.P(
                                                                    f"Moderate Traffic: {len(device_patterns.get('device_classifications', {}).get('moderate_traffic_devices', []))}"
                                                                ),
                                                                html.P(
                                                                    f"Low Traffic: {len(device_patterns.get('device_classifications', {}).get('low_traffic_devices', []))}"
                                                                ),
                                                            ],
                                                            width=6,
                                                        ),
                                                        dbc.Col(
                                                            [
                                                                html.H5(
                                                                    "Security Status"
                                                                ),
                                                                html.P(
                                                                    f"Secure Devices: {len(device_patterns.get('device_classifications', {}).get('secure_devices', []))}"
                                                                ),
                                                                html.P(
                                                                    f"Popular Devices: {len(device_patterns.get('device_classifications', {}).get('popular_devices', []))}"
                                                                ),
                                                                html.P(
                                                                    f"Problematic: {len(device_patterns.get('device_classifications', {}).get('problematic_devices', []))}"
                                                                ),
                                                            ],
                                                            width=6,
                                                        ),
                                                    ]
                                                )
                                            )
                                        ),
                                    ]
                                ),
                                width=6,
                            ),
                        ]
                    ),
                    html.Hr(),
                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.Card(
                                    [
                                        dbc.CardHeader(html.H4("Temporal Patterns")),
                                        dbc.CardBody(
                                            [
                                                html.P(
                                                    f"Peak Hours: {', '.join(map(str, temporal_patterns.get('peak_hours', [])))}"
                                                ),
                                                html.P(
                                                    f"Peak Days: {', '.join(temporal_patterns.get('peak_days', []))}"
                                                ),
                                                html.H6("Hourly Distribution:"),
                                                html.Div(
                                                    [
                                                        html.Span(
                                                            f"{hour}h: {count} ",
                                                            className="badge badge-secondary me-1",
                                                        )
                                                        for hour, count in sorted(
                                                            temporal_patterns.get(
                                                                "hourly_distribution",
                                                                {},
                                                            ).items()
                                                        )
                                                    ]
                                                ),
                                            ]
                                        ),
                                    ]
                                ),
                                width=8,
                            ),
                            dbc.Col(
                                dbc.Card(
                                    [
                                        dbc.CardHeader(html.H4("Key Statistics")),
                                        dbc.CardBody(
                                            [
                                                html.P(
                                                    f"Success Rate: {access_patterns.get('overall_success_rate', 0):.1%}"
                                                ),
                                                html.P(
                                                    f"Users w/ Low Success: {access_patterns.get('users_with_low_success', 0)}"
                                                ),
                                                html.P(
                                                    f"Devices w/ Issues: {access_patterns.get('devices_with_low_success', 0)}"
                                                ),
                                                html.P(
                                                    f"Avg Doors/User: {user_patterns.get('user_statistics', {}).get('mean_doors_per_user', 0):.1f}"
                                                ),
                                            ]
                                        ),
                                    ]
                                ),
                                width=4,
                            ),
                        ]
                    ),
                    html.Hr(),
                    html.H4("Recommendations", className="mb-3"),
                    (
                        html.Div(
                            [
                                dbc.Alert(
                                    [
                                        html.H5(
                                            f"{rec['category']} - {rec['priority']} Priority",
                                            className="alert-heading",
                                        ),
                                        html.P(rec["recommendation"]),
                                        html.Hr(),
                                        html.P(
                                            f"Action: {rec['action']}",
                                            className="mb-0",
                                        ),
                                    ],
                                    color=(
                                        "warning"
                                        if rec["priority"] == "High"
                                        else "info"
                                    ),
                                )
                                for rec in recommendations
                            ]
                        )
                        if recommendations
                        else dbc.Alert(
                            "No specific recommendations at this time.",
                            color="success",
                        )
                    ),
                    html.Hr(),
                    html.P(
                        f"Analysis completed at: {results.get('analysis_timestamp', 'N/A')}",
                        className="text-muted",
                    ),
                ]
            )
        elif results["status"] == "no_data":
            return dbc.Alert(
                [
                    html.H4("No Data Available"),
                    html.P("No processed data found for analysis."),
                    html.P("Please ensure:"),
                    html.Ul(
                        [
                            html.Li("Data files have been uploaded"),
                            html.Li("Column mapping has been completed"),
                            html.Li("Device mapping has been completed"),
                        ]
                    ),
                ],
                color="warning",
            )
        else:
            return dbc.Alert(
                [
                    html.H4("Analysis Failed"),
                    html.P(f"Error: {results.get('message', 'Unknown error')}"),
                    html.P("Please check the system logs for more details."),
                ],
                color="danger",
            )
    except Exception as e:  # pragma: no cover - safety net for unexpected errors
        return dbc.Alert(
            [
                html.H4("System Error"),
                html.P(f"Exception: {str(e)}"),
                html.P("Please check your configuration and try again."),
            ],
            color="danger",
        )


def dispatch_analysis(button_id: str, data_source: str):
    """Dispatch analysis based on clicked button."""

    analysis_map = {
        "security-btn": "security",
        "trends-btn": "trends",
        "behavior-btn": "behavior",
        "anomaly-btn": "anomaly",
        "suggests-btn": "suggests",
        "quality-btn": "quality",
        "unique-patterns-btn": "unique_patterns",
    }

    analysis_type = analysis_map.get(button_id)
    if not analysis_type:
        return dbc.Alert("Unknown analysis type", color="danger")

    dispatch = {
        "suggests": lambda: run_suggests_analysis(data_source),
        "quality": lambda: run_quality_analysis(data_source),
        "unique_patterns": lambda: run_unique_patterns_analysis(data_source),
        "security": lambda: run_service_analysis(data_source, "security"),
        "trends": lambda: run_service_analysis(data_source, "trends"),
        "behavior": lambda: run_service_analysis(data_source, "behavior"),
        "anomaly": lambda: run_service_analysis(data_source, "anomaly"),
    }

    return dispatch[analysis_type]()


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

        return get_data_source_options_safe()

    def update_status_alert(self, trigger):
        """Update status based on service health."""
        try:
            service = get_analytics_service_safe()
            suggests_available = AI_SUGGESTIONS_AVAILABLE

            if service and suggests_available:
                return "✅ All services available - Full functionality enabled"
            elif suggests_available:
                return "⚠️ Analytics service limited - AI suggestions available"
            elif service:
                return "⚠️ AI suggestions unavailable - Analytics service available"
            else:
                return "🔄 Running in limited mode - Some features may be unavailable"
        except Exception:
            return "❌ Service status unknown"


# =============================================================================
# SECTION 7: HELPER DISPLAY FUNCTIONS
# Add these helper functions for non-suggests analysis types
# =============================================================================


def register_callbacks(
    manager: "TrulyUnifiedCallbacks",
    controller: UnifiedAnalyticsController | None = None,
) -> None:
    """Instantiate :class:`Callbacks` and register its methods."""

    cb = Callbacks()

    callback_manager.register_operation(
        "analysis_buttons",
        lambda s, t, b, a, sug, q, u, ds: cb.handle_analysis_buttons(
            s, t, b, a, sug, q, u, ds
        ),
        name="handle_analysis_buttons",
        timeout=5,
    )
    callback_manager.register_operation(
        "refresh_sources",
        lambda n: cb.refresh_data_sources_callback(n),
        name="refresh_data_sources",
    )
    callback_manager.register_operation(
        "status_alert",
        lambda val: cb.update_status_alert(val),
        name="update_status_alert",
    )

    @manager.unified_callback(
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
        callback_id="analytics_operations",
        component_name="deep_analytics",
        prevent_initial_call=True,
    )
    def analytics_operations(
        sec, trn, beh, anom, sug, qual, uniq, refresh, trigger, data_source
    ):
        display = callback_manager.execute_group(
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

        options = callback_manager.execute_group("refresh_sources", refresh)[0]

        alert = callback_manager.execute_group("status_alert", trigger)[0]

        analytics_state.dispatch(
            "UPDATE", {"display": display, "options": options, "alert": alert}
        )

        return display, options, alert

    if controller is not None:
        controller.register_callback(
            "on_analysis_error",
            lambda aid, err: logger.error("Deep analytics error: %s", err),
        )


__all__ = ["Callbacks", "register_callbacks"]
