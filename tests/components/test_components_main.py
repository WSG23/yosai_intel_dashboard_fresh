import pytest
from dash import html
import components as comp

pytestmark = pytest.mark.usefixtures("fake_dash", "fake_dbc")


def test_create_loading_spinner(monkeypatch):
    # ensure Spinner component exists in stub
    monkeypatch.setattr(comp.dbc, "Spinner", lambda *a, **k: html.Div(), raising=False)
    monkeypatch.setattr(comp.html, "P", html.Div, raising=False)
    spinner = comp.create_loading_spinner("Wait")
    assert isinstance(spinner, html.Div)
    assert spinner.children


def test_component_registry_basic():
    reg = comp.ComponentRegistry()
    reg.register_component("dummy", lambda: "ok")
    assert reg.get_component("dummy")() == "ok"


def test_create_summary_cards(monkeypatch):
    monkeypatch.setattr(comp.html, "H4", html.H5, raising=False)
    monkeypatch.setattr(comp.html, "P", html.Span, raising=False)
    data = {
        "total_events": 5,
        "active_users": 2,
        "active_doors": 1,
        "date_range": {"start": "2024-01-01", "end": "2024-01-31"},
    }
    cards = comp.create_summary_cards(data)
    assert cards.children
