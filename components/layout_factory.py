from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import html


def card(title: str, body, color: str = "primary", icon: str | None = None, **kwargs):
    """Return a simple Bootstrap card.

    Parameters
    ----------
    title: str
        Card title text.
    body: Any
        Card body content. Can be a Dash component, list of components or
        plain text.
    color: str
        Bootstrap color scheme.
    icon: str | None
        Optional CSS class for an icon displayed before the title.
    kwargs: Any
        Additional arguments passed to :class:`dbc.Card`.
    """
    # Normalize body into list of components
    if isinstance(body, (str, bytes)):
        body_children = [html.P(body, className="card-text")]
    elif isinstance(body, (list, tuple)):
        body_children = list(body)
    else:
        body_children = [body]

    title_children = []
    if icon:
        title_children.append(
            html.I(className=f"{icon} me-2", **{"aria-hidden": "true"})
        )
    title_children.append(title)

    body_children.insert(0, html.H5(title_children, className="card-title"))

    kwargs.setdefault("className", "mb-4")

    return dbc.Card(dbc.CardBody(body_children), color=color, **kwargs)
