import pytest
import dash
import importlib.util
from pathlib import Path
from flask import Flask

pytestmark = pytest.mark.usefixtures("fake_dash")

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
    return dash.Dash()


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


def test_ensure_all_navbar_assets_without_pillow(tmp_path, monkeypatch):
    monkeypatch.setattr(assets_utils, "ASSET_ICON_DIR", tmp_path)

    import builtins

    original_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name.startswith("PIL"):
            raise ImportError("no pillow")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    assets_utils.ensure_all_navbar_assets()

    for icon in [
        "analytics.png",
        "graphs.png",
        "export.png",
        "settings.png",
        "upload.png",
    ]:
        assert (tmp_path / icon).exists()

    assert (tmp_path / "analytics.svg").is_file()


def test_ensure_navbar_assets_summary(tmp_path, monkeypatch):
    monkeypatch.setattr(assets_utils, "ASSET_ICON_DIR", tmp_path)

    def dummy_check(names, warn=True):
        return {name: (tmp_path / f"{name}.png").is_file() for name in names}

    monkeypatch.setattr(assets_utils, "check_navbar_assets", dummy_check)

    import builtins

    original_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name.startswith("PIL"):
            raise ImportError("no pillow")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    summary = assets_utils.ensure_navbar_assets()
    assert all(summary.values())
    assert (tmp_path / "analytics.svg").is_file()
