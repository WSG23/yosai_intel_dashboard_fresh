"""Dash components for plugin performance visualization."""
from __future__ import annotations

from dash import html, dcc, dash_table


class PluginPerformanceDashboard:
    """Generate plugin performance dashboard layouts."""

    def create_performance_overview(self) -> html.Div:
        return html.Div(id='plugin-performance-overview')

    def create_plugin_metrics_graph(self, plugin_name: str) -> dcc.Graph:
        return dcc.Graph(id=f'{plugin_name}-performance-graph')

    def create_performance_comparison_table(self) -> dash_table.DataTable:
        return dash_table.DataTable(id='plugin-performance-table')

    def create_alert_status_indicator(self) -> html.Div:
        return html.Div(id='plugin-performance-alerts')

