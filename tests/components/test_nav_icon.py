from dash import html

from components.ui.navbar import get_simple_icon


def test_get_simple_icon_returns_icon():
    comp = get_simple_icon("dashboard")
    assert isinstance(comp, html.I)
    assert "nav-icon" in getattr(comp, "className", "")


def test_get_simple_icon_fallback():
    comp = get_simple_icon("unknown")
    assert "fa-circle" in getattr(comp, "className", "")
