import pytest
from dash import html

from components.ui.navbar import create_navbar_layout, register_navbar_callbacks

pytestmark = pytest.mark.usefixtures("fake_dash", "fake_dbc")


class StubManager:
    def __init__(self):
        self.registered = []

    def handle_register(self, *args, **kwargs):
        def decorator(func):
            self.registered.append(kwargs.get("callback_id"))
            return func
        return decorator


def test_create_navbar_layout_accepts_custom_links_icons():
    links = {"Foo": "/foo"}
    icons = {"Foo": html.Span(id="foo-icon")}
    layout = create_navbar_layout(links=links, icons=icons)
    nav = layout.children.children[1]
    link = nav.children[0].children
    assert link.href == "/foo"
    assert getattr(link.children[0][0], "id", None) == "foo-icon"


def test_register_navbar_callbacks_connects_toggle():
    mgr = StubManager()
    register_navbar_callbacks(mgr)
    assert "navbar_toggle" in mgr.registered
