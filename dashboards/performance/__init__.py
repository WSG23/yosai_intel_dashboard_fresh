"""Simple performance dashboard placeholder."""

import dash_bootstrap_components as dbc
import pandas as pd
from dash import html

from yosai_intel_dashboard.src.components.analytics import (
    create_anomaly_trend_graph,
    create_baseline_table,
    create_mitre_attack_table,
    create_realtime_ws,
)


def layout() -> dbc.Container:
    """Render the performance metrics dashboard with analytics."""
    baseline_df = pd.DataFrame(
        [
            {"Metric": "Failed Rate", "Baseline": 0.05},
            {"Metric": "Badge Issues", "Baseline": 0.02},
            {"Metric": "After Hours", "Baseline": 0.05},
            {"Metric": "Weekend", "Baseline": 0.25},
        ]
    )

    anomaly_df = pd.DataFrame({"timestamp": [], "score": []})
    mitre_mapping: list[dict[str, str]] = []

    return dbc.Container(
        [
            html.H2("Performance Dashboard"),
            create_realtime_ws(),
            create_baseline_table(baseline_df),
            create_anomaly_trend_graph(anomaly_df),
            create_mitre_attack_table(mitre_mapping),
        ],
        fluid=True,
    )


__all__ = ["layout"]
