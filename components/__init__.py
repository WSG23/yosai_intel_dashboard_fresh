#!/usr/bin/env python3
"""
Simplified Component System
Replaces: Complex component registry, missing components, safe imports
"""
import logging
from typing import Any, Dict, List, Optional

import dash_bootstrap_components as dbc

if not hasattr(dbc, "Alert"):

    class _DummyComponent:
        def __init__(self, *a, **k):
            pass

    dbc.Alert = _DummyComponent  # type: ignore[attr-defined]
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html

from core.container import container
from core.protocols import ConfigurationProtocol

# from components.analytics.real_time_dashboard import RealTimeAnalytics

try:  # Prefer configuration from the DI container when available
    _cfg = container.get("config_manager", ConfigurationProtocol)
except Exception:  # pragma: no cover - container not initialized
    _cfg = None

if not _cfg:
    try:
        from config.dynamic_config import (
            dynamic_config as _cfg,  # type: ignore
        )
    except Exception:  # pragma: no cover - optional config
        _cfg = None

from yosai_intel_dashboard.src.infrastructure.config.constants import (
    MAX_DISPLAY_ROWS as DEFAULT_MAX_DISPLAY_ROWS,
)

if _cfg is not None and hasattr(_cfg, "analytics"):
    MAX_DISPLAY_ROWS = getattr(
        _cfg.analytics, "max_display_rows", DEFAULT_MAX_DISPLAY_ROWS
    )
    _MAX_UPLOAD_BYTES = getattr(_cfg.security, "max_upload_mb", 50) * 1024 * 1024
else:  # pragma: no cover - fallback for optional config
    MAX_DISPLAY_ROWS = DEFAULT_MAX_DISPLAY_ROWS
    _MAX_UPLOAD_BYTES = 50 * 1024 * 1024

logger = logging.getLogger(__name__)


# =============================================================================
# Analytics Components
# =============================================================================


def create_summary_cards(analytics_data: Dict[str, Any]) -> html.Div:
    """Create summary statistic cards for uploaded data."""
    if not analytics_data:
        return html.Div("No analytics data available")

    logger.info(f"📊 Creating summary cards from: {analytics_data.keys()}")

    cards = []

    # Total events card
    total_events = analytics_data.get("total_events", 0)
    logger.info(f"   Total events: {total_events}")
    cards.append(
        dbc.Col(
            [
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.H4(
                                    f"{total_events:,}", className="text-primary mb-0"
                                ),
                                html.P("Total Events", className="text-muted mb-0"),
                            ]
                        )
                    ]
                )
            ],
            width=3,
        )
    )

    # Active users using multiple fallbacks
    active_users = (
        analytics_data.get("active_users", 0)
        or analytics_data.get("unique_users", 0)
        or len(analytics_data.get("top_users", []))
    )
    logger.info(f"   Active users: {active_users}")
    cards.append(
        dbc.Col(
            [
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.H4(
                                    f"{active_users:,}", className="text-success mb-0"
                                ),
                                html.P("Active Users", className="text-muted mb-0"),
                            ]
                        )
                    ]
                )
            ],
            width=3,
        )
    )

    # Active doors using multiple fallbacks
    active_doors = (
        analytics_data.get("active_doors", 0)
        or analytics_data.get("unique_doors", 0)
        or len(analytics_data.get("top_doors", []))
    )
    logger.info(f"   Active doors: {active_doors}")
    cards.append(
        dbc.Col(
            [
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.H4(
                                    f"{active_doors:,}", className="text-warning mb-0"
                                ),
                                html.P("Active Doors", className="text-muted mb-0"),
                            ]
                        )
                    ]
                )
            ],
            width=3,
        )
    )

    # Date Range Card
    date_range = analytics_data.get("date_range", {})
    if date_range and date_range.get("start"):
        date_text = f"{date_range['start']} to {date_range.get('end', 'now')}"
        cards.append(
            dbc.Col(
                [
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.H6(date_text, className="text-info mb-0"),
                                    html.P("Date Range", className="text-muted mb-0"),
                                ]
                            )
                        ]
                    )
                ],
                width=3,
            )
        )

    return (
        dbc.Row(cards, className="mb-4")
        if cards
        else html.Div("No data for summary cards")
    )


def create_analytics_charts(analytics_data: Dict[str, Any]) -> html.Div:
    """Create analytics charts from data"""
    if not analytics_data:
        return html.Div("No data available for charts")

    charts = []

    # Top Users Chart
    top_users = analytics_data.get("top_users", [])
    if top_users:
        try:
            df_users = pd.DataFrame(top_users)
            if (
                not df_users.empty
                and "user_id" in df_users.columns
                and "count" in df_users.columns
            ):
                fig_users = px.bar(
                    df_users.head(10),
                    x="user_id",
                    y="count",
                    title="Top 10 Users by Activity",
                    template="plotly_white",
                )
                fig_users.update_layout(
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                    font=dict(color="black", size=12),
                    title_font=dict(color="black", size=16),
                )
                fig_users.update_xaxes(tickfont=dict(color="black"))
                fig_users.update_yaxes(tickfont=dict(color="black"))

                charts.append(
                    dbc.Col(
                        [dbc.Card([dbc.CardBody([dcc.Graph(figure=fig_users)])])],
                        width=6,
                    )
                )
        except Exception as e:
            logger.warning(f"Error creating users chart: {e}")

    # Top Doors Chart
    top_doors = analytics_data.get("top_doors", [])
    if top_doors:
        try:
            df_doors = pd.DataFrame(top_doors)
            if (
                not df_doors.empty
                and "door_id" in df_doors.columns
                and "count" in df_doors.columns
            ):
                fig_doors = px.bar(
                    df_doors.head(10),
                    x="door_id",
                    y="count",
                    title="Top 10 Doors by Access Count",
                    template="plotly_white",
                )
                fig_doors.update_layout(
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                    font=dict(color="black", size=12),
                    title_font=dict(color="black", size=16),
                )
                fig_doors.update_xaxes(tickfont=dict(color="black"))
                fig_doors.update_yaxes(tickfont=dict(color="black"))

                charts.append(
                    dbc.Col(
                        [dbc.Card([dbc.CardBody([dcc.Graph(figure=fig_doors)])])],
                        width=6,
                    )
                )
        except Exception as e:
            logger.warning(f"Error creating doors chart: {e}")

    # Access Patterns Chart
    access_patterns = analytics_data.get("access_patterns", {})
    if access_patterns:
        try:
            patterns_df = pd.DataFrame(
                [{"Pattern": k, "Count": v} for k, v in access_patterns.items()]
            )

            if not patterns_df.empty:
                fig_patterns = px.pie(
                    patterns_df,
                    values="Count",
                    names="Pattern",
                    title="Access Patterns Distribution",
                    template="plotly_white",
                )
                fig_patterns.update_layout(
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                    font=dict(color="black", size=12),
                    title_font=dict(color="black", size=16),
                )

                charts.append(
                    dbc.Col(
                        [dbc.Card([dbc.CardBody([dcc.Graph(figure=fig_patterns)])])],
                        width=12,
                    )
                )
        except Exception as e:
            logger.warning(f"Error creating patterns chart: {e}")

    # Arrange charts in rows
    if not charts:
        return html.Div("No charts could be generated from the data")

    # Group charts into rows of 2
    rows = []
    for i in range(0, len(charts), 2):
        if i + 1 < len(charts):
            rows.append(dbc.Row([charts[i], charts[i + 1]], className="mb-4"))
        else:
            rows.append(dbc.Row([charts[i]], className="mb-4"))

    return html.Div(rows)


def create_data_preview(df: pd.DataFrame, filename: str = "") -> html.Div:
    """Create data preview component.

    The preview table always uses ``df.head(5)`` and the DataFrame is
    clamped to fewer than 100 rows before rendering.
    """
    if df is None or df.empty:
        return dbc.Alert("No data to preview", color="info")

    # Clamp to avoid huge previews
    df_limited = df.head(MAX_DISPLAY_ROWS) if len(df) > MAX_DISPLAY_ROWS else df
    df = df_limited.head(99)
    num_rows, num_cols = df.shape

    return dbc.Card(
        [
            dbc.CardHeader([html.H5(f"📄 Data Preview: {filename}", className="mb-0")]),
            dbc.CardBody(
                [
                    html.P(
                        f"Shape: {num_rows:,} rows × {num_cols} columns",
                        className="text-muted",
                    ),
                    # Column info
                    html.H6("Columns:", className="mt-3"),
                    html.Ul(
                        [
                            html.Li(f"{col} ({str(df[col].dtype)})")
                            for col in df.columns[:10]  # Show first 10 columns
                        ]
                    ),
                    # Data preview table
                    html.H6("Sample Data:", className="mt-3"),
                    dbc.Table.from_dataframe(
                        df_limited.head(5),
                        striped=True,
                        bordered=True,
                        hover=True,
                        responsive=True,
                        size="sm",
                    ),
                ]
            ),
        ],
        className="mb-4",
    )


# =============================================================================
# File Upload Components
# =============================================================================


def create_file_uploader() -> html.Div:
    """Create file upload component"""
    return dbc.Card(
        [
            dbc.CardBody(
                [
                    html.H5("Upload Data Files", className="mb-3"),
                    dcc.Upload(
                        id="upload-data",
                        max_size=_MAX_UPLOAD_BYTES,
                        children=html.Div(
                            [
                                html.I(
                                    className="fas fa-cloud-upload-alt fa-3x mb-3 text-primary",
                                    **{"aria-hidden": "true"},
                                ),
                                html.H6("Drag and Drop or Click to Select Files"),
                                html.P(
                                    "Supports CSV, Excel, JSON files",
                                    className="text-muted",
                                ),
                            ],
                            className="text-center p-4",
                        ),
                        className="upload-simple",
                        multiple=True,
                    ),
                    html.Div(id="upload-output", className="mt-3"),
                ]
            )
        ]
    )


# =============================================================================
# Utility Functions
# =============================================================================


def create_loading_spinner(text: str = "Loading...") -> html.Div:
    """Create loading spinner component"""
    return html.Div(
        [
            dbc.Spinner(size="lg", color="primary"),
            html.P(text, className="mt-2 text-muted"),
        ],
        className="text-center p-4",
    )


def create_error_alert(message: str, title: str = "Error") -> dbc.Alert:
    """Create error alert component"""
    return dbc.Alert(
        [
            html.H6(title, className="alert-heading"),
            html.P(message, className="mb-0"),
        ],
        color="danger",
    )


def create_success_alert(message: str, title: str = "Success") -> dbc.Alert:
    """Create success alert component"""
    return dbc.Alert(
        [
            html.H6(title, className="alert-heading"),
            html.P(message, className="mb-0"),
        ],
        color="success",
    )


def create_info_alert(message: str, title: str = "Info") -> dbc.Alert:
    """Create info alert component"""
    return dbc.Alert(
        [
            html.H6(title, className="alert-heading"),
            html.P(message, className="mb-0"),
        ],
        color="info",
    )


# =============================================================================
# Analytics Data Generation
# =============================================================================


def generate_sample_analytics() -> Dict[str, Any]:
    """Generate sample analytics data for testing"""
    import random
    from datetime import datetime, timedelta

    # Generate sample users
    users = []
    for i in range(20):
        users.append({"user_id": f"user_{i+1:03d}", "count": random.randint(5, 50)})

    # Generate sample doors
    doors = []
    door_names = [
        "main_entrance",
        "parking_gate",
        "office_door",
        "server_room",
        "cafeteria",
    ]
    for door in door_names:
        doors.append({"door_id": door, "count": random.randint(10, 100)})

    # Generate access patterns
    patterns = {
        "Normal Access": random.randint(300, 500),
        "After Hours": random.randint(20, 80),
        "Failed Attempts": random.randint(5, 25),
        "Emergency Exit": random.randint(1, 10),
    }

    # Date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    return {
        "total_events": sum(user["count"] for user in users),
        "top_users": sorted(users, key=lambda x: x["count"], reverse=True),
        "top_doors": sorted(doors, key=lambda x: x["count"], reverse=True),
        "access_patterns": patterns,
        "date_range": {
            "start": start_date.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d"),
        },
    }


# =============================================================================
# Component Registry (Simplified)
# =============================================================================


class ComponentRegistry:
    """Simple component registry"""

    def __init__(self):
        self.components = {
            "summary_cards": create_summary_cards,
            "analytics_charts": create_analytics_charts,
            "data_preview": create_data_preview,
            "file_uploader": create_file_uploader,
            "loading_spinner": create_loading_spinner,
            "error_alert": create_error_alert,
            "success_alert": create_success_alert,
            "info_alert": create_info_alert,
            "sample_analytics": generate_sample_analytics,
            #             "realtime_analytics": RealTimeAnalytics,
        }

    def get_component(self, name: str):
        """Get component by name"""
        return self.components.get(name)

    def register_component(self, name: str, component):
        """Register new component"""
        self.components[name] = component


# Global registry instance
_registry = ComponentRegistry()


def get_component(name: str):
    """Get component from global registry"""
    return _registry.get_component(name)


def register_component(name: str, component):
    """Register component in global registry"""
    _registry.register_component(name, component)


# Export all components and functions
__all__ = [
    "create_summary_cards",
    "create_analytics_charts",
    "create_data_preview",
    "create_file_uploader",
    "create_loading_spinner",
    "create_error_alert",
    "create_success_alert",
    "create_info_alert",
    "generate_sample_analytics",
    "ComponentRegistry",
    "get_component",
    "register_component",
    #     "RealTimeAnalytics",
]
