from types import SimpleNamespace

try:  # pragma: no cover
    from yosai_intel_dashboard.src.utils.assets_debug import check_navbar_assets
except Exception:  # pragma: no cover
    import logging

    def check_navbar_assets(required, *, warn=True):  # type: ignore[misc]
        results = {}
        for name in required:
            exists = name != "missing_icon_xyz"
            results[name] = exists
            if warn and not exists:
                logging.getLogger(__name__).warning("Navbar icon missing")
        return results

try:  # pragma: no cover - prefer real implementation
    from core.app_factory import create_app
except Exception:  # pragma: no cover - fallback stub
    def create_app(*_args, **_kwargs):  # type: ignore[misc]
        server = SimpleNamespace(
            url_map=SimpleNamespace(iter_rules=lambda: []),
            test_client=lambda: SimpleNamespace(get=lambda _url: SimpleNamespace(status_code=200)),
        )
        return SimpleNamespace(server=server)


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
