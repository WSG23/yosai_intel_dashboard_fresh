#!/usr/bin/env python3
"""
UI components for file preview - Separated from processing logic
"""
from typing import Any, Dict, List

import dash_bootstrap_components as dbc
from dash import dash_table, html


def create_file_preview_ui(preview_info: Dict[str, Any]) -> dbc.Card:
    """Create UI preview component from processed file data"""
    if not preview_info.get('preview_data'):
        return dbc.Card(
            dbc.CardBody("No preview data available"),
            className="mt-3"
        )

    columns = [{"name": col, "id": col} for col in preview_info['columns']]

    return dbc.Card([
        dbc.CardHeader(
            html.H5(f"Preview ({preview_info['total_rows']} total rows)")
        ),
        dbc.CardBody([
            dash_table.DataTable(
                data=preview_info['preview_data'],
                columns=columns,
                style_cell={'textAlign': 'left'},
                style_header={'backgroundColor': 'rgb(230, 230, 230)'},
                page_size=10
            )
        ])
    ], className="mt-3")
