"""Reusable analytic visualization components."""

from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
import pandas as pd
import plotly.graph_objs as go
from dash import dash_table, dcc, html


def create_baseline_table(baseline: pd.DataFrame) -> dash_table.DataTable:
    """Return a table displaying baseline behavior metrics."""
    return dash_table.DataTable(
        id="behavior-baseline-table",
        data=baseline.to_dict("records"),
        columns=[{"name": c, "id": c} for c in baseline.columns],
        style_table={"overflowX": "auto"},
    )


def create_anomaly_trend_graph(anomalies: pd.DataFrame) -> dcc.Graph:
    """Return a line graph of anomaly scores over time."""
    fig = go.Figure(
        data=go.Scatter(
            x=anomalies["timestamp"],
            y=anomalies["score"],
            mode="lines+markers",
            line=dict(color="var(--graph-series-4)"),
        )
    )
    fig.update_layout(
        title="Anomaly Trend",
        xaxis_title="Time",
        yaxis_title="Score",
    )
    return dcc.Graph(id="anomaly-trend-graph", figure=fig)


def create_mitre_attack_table(mappings: List[Dict[str, Any]]) -> dash_table.DataTable:
    """Return a table mapping events to MITRE ATT&CK techniques."""
    return dash_table.DataTable(
        id="mitre-attack-table",
        data=mappings,
        columns=[
            {"name": "Technique", "id": "technique"},
            {"name": "Tactic", "id": "tactic"},
            {"name": "Description", "id": "description"},
        ],
        style_table={"overflowX": "auto"},
    )


def create_realtime_ws(url: str = "/ws") -> html.Div:
    """WebSocket component for real-time updates."""
    return html.Div(
        [dcc.Location(id="ws-url", pathname=url), html.Div(id="ws-placeholder")],
        id="ws-container",
    )


def create_timeline_graph(df: pd.DataFrame, x_col: str, y_col: str) -> dcc.Graph:
    """Return a simple timeline chart."""
    fig = go.Figure(data=go.Scatter(x=df[x_col], y=df[y_col], mode="lines+markers"))
    fig.update_layout(title="Timeline", xaxis_title=x_col, yaxis_title=y_col)
    return dcc.Graph(id="timeline-graph", figure=fig)


def create_heatmap(data: pd.DataFrame) -> dcc.Graph:
    """Return a heat map of day vs hour."""
    fig = go.Figure(
        data=go.Heatmap(
            z=data.values, x=data.columns, y=data.index, colorscale="Viridis"
        )
    )
    fig.update_layout(title="Activity Heatmap", xaxis_title="Hour", yaxis_title="Day")
    return dcc.Graph(id="activity-heatmap", figure=fig)


def create_network_graph(nodes: List[str], edges: List[tuple]) -> dcc.Graph:
    """Return a simple network graph."""
    node_x, node_y = [], []
    angle = np.linspace(0, 2 * np.pi, len(nodes), endpoint=False)
    radius = 1.0
    for ang in angle:
        node_x.append(radius * np.cos(ang))
        node_y.append(radius * np.sin(ang))

    edge_x, edge_y = [], []
    for src, dst in edges:
        edge_x += [node_x[src], node_x[dst], None]
        edge_y += [node_y[src], node_y[dst], None]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=edge_x, y=edge_y, mode="lines", line=dict(color="#888")))
    fig.add_trace(go.Scatter(x=node_x, y=node_y, mode="markers+text", text=nodes))
    fig.update_layout(showlegend=False, title="Access Network")
    return dcc.Graph(id="network-graph", figure=fig)


__all__ = [
    "create_baseline_table",
    "create_anomaly_trend_graph",
    "create_mitre_attack_table",
    "create_realtime_ws",
    "create_timeline_graph",
    "create_heatmap",
    "create_network_graph",
]
