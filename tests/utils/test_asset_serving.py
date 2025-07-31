import os

from core.app_factory import create_app
from yosai_intel_dashboard.src.utils import debug_dash_asset_serving


def test_debug_dash_asset_serving(monkeypatch):
    monkeypatch.setenv("YOSAI_ENV", "development")
    monkeypatch.setenv("SECRET_KEY", "test")
    app = create_app(mode="simple")
    assert debug_dash_asset_serving(app) is True
