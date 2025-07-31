from core.app_factory import create_app
from yosai_intel_dashboard.src.utils.assets_debug import check_navbar_assets


def _make_app(monkeypatch):
    monkeypatch.setenv("YOSAI_ENV", "development")
    monkeypatch.setenv("SECRET_KEY", "test")
    return create_app(mode="simple")


def test_check_navbar_assets_warn(monkeypatch, caplog):
    _make_app(monkeypatch)
    with caplog.at_level("WARNING"):
        result = check_navbar_assets(["analytics", "missing_icon_xyz"])
    assert result["analytics"] is True
    assert result["missing_icon_xyz"] is False
    assert any("Navbar icon missing" in r.getMessage() for r in caplog.records)


def test_check_navbar_assets_no_warn(monkeypatch, caplog):
    _make_app(monkeypatch)
    with caplog.at_level("WARNING"):
        result = check_navbar_assets(["missing_icon_xyz"], warn=False)
    assert result == {"missing_icon_xyz": False}
    assert not caplog.records
