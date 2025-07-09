from dash import html

from components.ui.navbar import get_simple_icon


def test_get_simple_icon_returns_component():
    comp = get_simple_icon("analytics")
    assert "nav-icon" in getattr(comp, "className", "")
    assert isinstance(comp, (html.Img, html.Span))


def test_get_simple_icon_fallback():
    comp = get_simple_icon("unknown")
    assert "nav-icon" in getattr(comp, "className", "")
