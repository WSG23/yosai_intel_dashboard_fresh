from core.app_factory import create_app
from utils.assets_utils import get_nav_icon


def _make_app(monkeypatch):
    monkeypatch.setenv("YOSAI_ENV", "development")
    monkeypatch.setenv("SECRET_KEY", "test")
    return create_app(mode="simple")


def test_get_nav_icon_existing(monkeypatch):
    app = _make_app(monkeypatch)
    assert get_nav_icon(app, "analytics") is not None


def test_get_nav_icon_missing(monkeypatch):
    app = _make_app(monkeypatch)
    assert get_nav_icon(app, "missing_icon_xyz") is None


