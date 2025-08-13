from __future__ import annotations

import importlib.machinery
import importlib.util
from pathlib import Path

_loader = importlib.machinery.SourceFileLoader(
    "env_module", str(Path("config/environment.py"))
)
_spec = importlib.util.spec_from_loader(_loader.name, _loader)
environment = importlib.util.module_from_spec(_spec)
_loader.exec_module(environment)

get_environment = environment.get_environment
select_config_file = environment.select_config_file


def test_get_environment_defaults_to_development(monkeypatch):
    monkeypatch.delenv("YOSAI_ENV", raising=False)
    assert get_environment() == "development"


def test_get_environment_staging(monkeypatch):
    monkeypatch.setenv("YOSAI_ENV", "STAGING-123")
    assert get_environment() == "staging"


def test_select_config_file_explicit(tmp_path, monkeypatch):
    path = tmp_path / "custom.yaml"
    path.write_text("a: 1")
    assert select_config_file(str(path)) == path


def test_select_config_file_env_var(monkeypatch, tmp_path):
    path = tmp_path / "env.yaml"
    path.write_text("b: 2")
    monkeypatch.setenv("YOSAI_CONFIG_FILE", str(path))
    assert select_config_file() == path


def test_select_config_file_from_environment(monkeypatch):
    monkeypatch.delenv("YOSAI_CONFIG_FILE", raising=False)
    monkeypatch.setenv("YOSAI_ENV", "production")
    expected = Path("config/environments/production.yaml")
    assert select_config_file() == expected


def test_select_config_file_unknown_env(monkeypatch):
    monkeypatch.delenv("YOSAI_CONFIG_FILE", raising=False)
    monkeypatch.setenv("YOSAI_ENV", "qa")
    expected = Path("config/config.yaml")
    assert select_config_file() == expected
