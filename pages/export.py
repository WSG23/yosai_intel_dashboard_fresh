#!/usr/bin/env python3
"""Export page providing download instructions."""

import dash_bootstrap_components as dbc
from dash import dcc, html, register_page as dash_register_page

from security.unicode_security_processor import sanitize_unicode_input


def register_page() -> None:
    """Register this page with Dash after app creation."""
    dash_register_page(__name__, path="/export", name="Export")


def _instructions() -> dbc.Card:
    """Return a card describing how to export learned data."""
    code_example = """```python
import services.export_service as export_service

data = export_service.get_enhanced_data()
csv_content = export_service.to_csv_string(data)
```"""

    return dbc.Card(
        [
            dbc.CardHeader(html.H4(sanitize_unicode_input("Exporting Data"))),
            dbc.CardBody(
                [
                    html.P(
                        "Use the export service to download mappings generated "
                        "from analytics results.",
                        className="mb-3",
                    ),
                    html.Ol(
                        [
                            html.Li(
                                "Fetch learned data with "
                                "`export_service.get_enhanced_data()`"
                            ),
                            html.Li(
                                "Convert to CSV or JSON using the helper " "functions",
                            ),
                            html.Li(
                                "Return the string through a `dcc.Download` "
                                "component",
                            ),
                        ],
                        className="mb-4",
                    ),
                    html.P(
                        "Exported files are saved by your browser to the default download"
                        " location, such as `~/Downloads`.",
                        className="mb-3",
                    ),
                    dcc.Markdown(code_example, className="bg-light p-3 rounded"),
                ]
            ),
            dbc.CardFooter("Design tokens ensure consistent styling"),
        ],
        className="shadow-sm",
    )


def layout() -> dbc.Container:
    """Export page layout with usage instructions."""
    return dbc.Container([_instructions()], fluid=True)


__all__ = ["layout", "register_page"]
