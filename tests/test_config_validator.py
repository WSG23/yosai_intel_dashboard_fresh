import pytest

import importlib.util
import importlib
import sys
from pathlib import Path
import types

pkg = types.ModuleType("config")
pkg.__path__ = [str(Path(__file__).resolve().parents[1] / "config")]
sys.modules.setdefault("config", pkg)

_cfg_path = Path(__file__).resolve().parents[1] / "config" / "config_manager.py"
spec = importlib.util.spec_from_file_location("config.config_manager", _cfg_path)
_cfg_module = importlib.util.module_from_spec(spec)
sys.modules["config.config_manager"] = _cfg_module
spec.loader.exec_module(_cfg_module)  # type: ignore
create_config_manager = _cfg_module.create_config_manager

from core.exceptions import ConfigurationError
from config.config_validator import ConfigValidator


def _write(tmp_path, text: str) -> str:
    p = tmp_path / "config.yaml"
    p.write_text(text)
    return str(p)


def test_missing_required_sections(monkeypatch, tmp_path):
    path = _write(tmp_path, "app:\n  title: Test")
    monkeypatch.setenv("YOSAI_CONFIG_FILE", path)
    monkeypatch.setenv("MAX_UPLOAD_MB", "50")
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
    monkeypatch.setenv("MAX_UPLOAD_MB", "50")
    with pytest.raises(ConfigurationError):
        create_config_manager()


def test_non_mapping_input():
    with pytest.raises(ConfigurationError):
        ConfigValidator.validate("bad")


def test_valid_config(monkeypatch, tmp_path):
    yaml_text = """
app:
  title: Test
database:
  name: test.db
security:
  secret_key: xyz
"""
    config_data = importlib.import_module("yaml").safe_load(yaml_text)
    cfg = ConfigValidator.validate(config_data)
    assert cfg.app.title == "Test"


def test_upload_limit_error():
    from config.base import Config

    cfg = Config()
    cfg.security.max_upload_mb = 0
    result = ConfigValidator.run_checks(cfg)
    assert result.valid is False
    assert "max_upload_mb" in result.errors[0]


def test_upload_limit_warning():
    from config.base import Config

    cfg = Config()
    cfg.security.max_upload_mb = 2000
    result = ConfigValidator.run_checks(cfg)
    assert result.valid is True
    assert any("max_upload_mb" in w for w in result.warnings)
