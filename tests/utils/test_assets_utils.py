import importlib.util
from pathlib import Path

import dash
import pytest
from flask import Flask

spec = importlib.util.spec_from_file_location(
    "assets_utils", Path(__file__).resolve().parents[2] / "utils" / "assets_utils.py"
)
assets_utils = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(assets_utils)
get_nav_icon = assets_utils.get_nav_icon
ensure_all_navbar_assets = assets_utils.ensure_all_navbar_assets


def _make_app(monkeypatch):
    monkeypatch.setenv("YOSAI_ENV", "development")
    return dash.Dash()


def test_get_nav_icon_always_none(monkeypatch):
    app = _make_app(monkeypatch)
    assert get_nav_icon(app, "analytics") is None


def test_get_nav_icon_flask_app(monkeypatch):
    flask_app = Flask(__name__)
    assert get_nav_icon(flask_app, "analytics") is None


def test_ensure_all_navbar_assets_creates_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(assets_utils, "ASSET_ICON_DIR", tmp_path)
    ensure_all_navbar_assets()
    assert tmp_path.exists()
