from dash import html


def layout():
    """Return the page layout."""
    return html.Div(
        [
            html.Div(id="name-input"),
            html.Div(id="greet-output"),
        ]
    )
