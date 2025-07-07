import importlib
import importlib.util
import sys
import types
from pathlib import Path

from dash import html


def _load_navbar_module():
    """Import navbar module with minimal utils stubs to avoid heavy deps."""
    if "test_navbar_module" in sys.modules:
        return sys.modules["test_navbar_module"]

    # Load real utils submodules without executing utils/__init__
    for name in ["assets_utils", "assets_debug"]:
        full_name = f"utils.{name}"
        if full_name not in sys.modules:
            spec = importlib.util.spec_from_file_location(
                full_name, Path("utils") / f"{name}.py"
            )
            mod = importlib.util.module_from_spec(spec)
            assert spec.loader is not None
            spec.loader.exec_module(mod)
            sys.modules[full_name] = mod

    spec = importlib.util.spec_from_file_location(
        "components.ui.navbar", Path("components/ui/navbar.py")
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    components_pkg = types.ModuleType("components")
    ui_pkg = types.ModuleType("components.ui")
    components_pkg.ui = ui_pkg
    ui_pkg.navbar = module
    sys.modules.setdefault("components", components_pkg)
    sys.modules.setdefault("components.ui", ui_pkg)
    sys.modules["components.ui.navbar"] = module
    return module


navbar = _load_navbar_module()
_nav_icon = navbar._nav_icon

# Provide minimal stub for core.app_factory.create_app to avoid heavy deps
core_app_factory = types.ModuleType("core.app_factory")


def _stub_create_app(mode: str | None = None):
    from dash import Dash

    app = Dash(__name__)
    app.get_asset_url = lambda path: f"/assets/{path}"
    return app


core_app_factory.create_app = _stub_create_app
sys.modules.setdefault("core.app_factory", core_app_factory)
from core.app_factory import create_app


def _make_app(monkeypatch):
    monkeypatch.setenv("YOSAI_ENV", "development")
    monkeypatch.setenv("SECRET_KEY", "test")
    return create_app(mode="simple")


def test_nav_icon_image(monkeypatch):
    app = _make_app(monkeypatch)
    comp = _nav_icon(app, "analytics", "Analytics")
    assert isinstance(comp, html.Img)
    assert "nav-icon--image" in comp.className


def test_nav_icon_fallback(monkeypatch):
    app = _make_app(monkeypatch)
    comp = _nav_icon(app, "missing", "Missing")
    assert isinstance(comp, html.I)
    assert "nav-icon--fallback" in comp.className
