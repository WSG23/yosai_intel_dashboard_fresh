import pytest
from config.config import ConfigManager


def test_plugin_config_loaded():
    cm = ConfigManager()
    plugins = cm.get_plugins_config()
    assert "json_serialization" in plugins
    assert plugins["json_serialization"]["enabled"] is True

