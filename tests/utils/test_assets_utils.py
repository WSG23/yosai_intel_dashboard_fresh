import dash
import importlib.util
from pathlib import Path
from flask import Flask

spec = importlib.util.spec_from_file_location(
    "assets_utils", Path(__file__).resolve().parents[2] / "utils" / "assets_utils.py"
)
assets_utils = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(assets_utils)
get_nav_icon = assets_utils.get_nav_icon


def _make_app(monkeypatch):
    # Create a minimal Dash app for testing
    monkeypatch.setenv("YOSAI_ENV", "development")
    return dash.Dash(__name__, assets_folder="assets")


def test_get_nav_icon_existing(monkeypatch):
    app = _make_app(monkeypatch)
    assert (
        get_nav_icon(app, "analytics")
        == "/assets/navbar_icons/analytics.png"
    )


def test_get_nav_icon_missing(monkeypatch):
    app = _make_app(monkeypatch)
    assert get_nav_icon(app, "missing_icon_xyz") is None


def test_get_nav_icon_fallback(monkeypatch):
    app = _make_app(monkeypatch)

    def raise_error(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(assets_utils, "url_for", raise_error)
    assert (
        get_nav_icon(app, "analytics")
        == "/assets/navbar_icons/analytics.png"
    )


def test_get_nav_icon_flask_app(monkeypatch):
    flask_app = Flask(__name__)
    assert (
        get_nav_icon(flask_app, "analytics")
        == "/assets/navbar_icons/analytics.png"
    )
