import pytest

from config import create_config_manager
from core.exceptions import ConfigurationError
from config.config_validator import ConfigValidator


def _write(tmp_path, text: str) -> str:
    p = tmp_path / "config.yaml"
    p.write_text(text)
    return str(p)


def test_missing_required_sections(monkeypatch, tmp_path):
    path = _write(tmp_path, "app:\n  title: Test")
    monkeypatch.setenv("YOSAI_CONFIG_FILE", path)
    with pytest.raises(ConfigurationError):
        create_config_manager()


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
        create_config_manager()


def test_non_mapping_input():
    with pytest.raises(ConfigurationError):
        ConfigValidator.validate("bad")


def test_valid_config(monkeypatch, tmp_path):
    yaml = """
app:
  title: Test
database:
  name: test.db
security:
  secret_key: xyz
"""
    path = _write(tmp_path, yaml)
    monkeypatch.setenv("YOSAI_CONFIG_FILE", path)
    cfg = create_config_manager()
    assert cfg.get_app_config().title == "Test"
