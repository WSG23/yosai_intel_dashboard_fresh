import importlib
import sys
import types

import pytest

import core.plugins.config as plugin_config


def test_fallback_service_locator():
    importlib.reload(plugin_config)
    assert plugin_config.get_service_locator() is None
    assert plugin_config.__all__ == ["get_service_locator"]


def test_imported_unified_config(monkeypatch):
    fake_module = types.ModuleType("config.unified_config")

    class DummyConfig:
        pass

    def get_config():
        return DummyConfig()

    fake_module.UnifiedConfig = DummyConfig
    fake_module.get_config = get_config
    monkeypatch.setitem(sys.modules, "config.unified_config", fake_module)
    importlib.reload(plugin_config)

    locator = plugin_config.get_service_locator()
    assert isinstance(locator, DummyConfig)
    assert "UnifiedConfig" in plugin_config.__all__

    monkeypatch.delitem(sys.modules, "config.unified_config", raising=False)
    importlib.reload(plugin_config)
