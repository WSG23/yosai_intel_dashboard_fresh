import pytest
from dash import html

from components.ui.navbar import _nav_icon
from tests.fake_navbar_factory import FakeNavbarFactory

factory = FakeNavbarFactory()


def test_nav_icon_image():
    comp = _nav_icon(factory, "analytics", "Analytics")
    assert isinstance(comp, html.Img)
    assert "nav-icon--image" in getattr(comp, "className", "")


def test_nav_icon_fallback():
    class MissingFactory(FakeNavbarFactory):
        def get_icon_url(self, app, name: str):
            return None

    comp = _nav_icon(MissingFactory(), "missing", "Missing")
    assert isinstance(comp, html.I)
    assert "nav-icon--fallback" in getattr(comp, "className", "")
