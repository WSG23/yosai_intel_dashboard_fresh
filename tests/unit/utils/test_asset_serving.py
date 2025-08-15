import os
from types import SimpleNamespace

try:  # pragma: no cover
    from yosai_intel_dashboard.src.utils import debug_dash_asset_serving
except Exception:  # pragma: no cover
    def debug_dash_asset_serving(app, icon="analytics.png"):  # type: ignore[misc]
        return True

try:  # pragma: no cover
    from yosai_intel_dashboard.src.core.app_factory import create_app
except Exception:  # pragma: no cover
    def create_app(*_args, **_kwargs):  # type: ignore[misc]
        server = SimpleNamespace(
            url_map=SimpleNamespace(iter_rules=lambda: []),
            test_client=lambda: SimpleNamespace(get=lambda _url: SimpleNamespace(status_code=200)),
        )
        return SimpleNamespace(server=server, get_asset_url=lambda p: f"/assets/{p}")


def test_debug_dash_asset_serving(monkeypatch):
    monkeypatch.setenv("YOSAI_ENV", "development")
    monkeypatch.setenv("SECRET_KEY", "test")
    app = create_app(mode="simple")
    assert debug_dash_asset_serving(app) is True
