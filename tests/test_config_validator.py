import pytest

from config.config import ConfigManager
from core.exceptions import ConfigurationError


def _write(tmp_path, text: str) -> str:
    p = tmp_path / "config.yaml"
    p.write_text(text)
    return str(p)


def test_missing_required_sections(monkeypatch, tmp_path):
    path = _write(tmp_path, "app:\n  title: Test")
    monkeypatch.setenv("YOSAI_CONFIG_FILE", path)
    with pytest.raises(ConfigurationError):
        ConfigManager()


def test_invalid_section_type(monkeypatch, tmp_path):
    yaml = """
app:
  title: Test
database: []
security:
  secret_key: abc
"""
    path = _write(tmp_path, yaml)
    monkeypatch.setenv("YOSAI_CONFIG_FILE", path)
    with pytest.raises(ConfigurationError):
        ConfigManager()
