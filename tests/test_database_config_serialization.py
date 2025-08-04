from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from types import ModuleType

import pytest
from cryptography.fernet import Fernet

pytest.importorskip("cryptography")


def _load_database_config():
    """Load DatabaseConfig without importing the heavy config package."""

    # Ensure real cryptography module is used
    sys.modules.pop("cryptography", None)
    sys.modules.pop("cryptography.fernet", None)

    repo_root = Path(__file__).resolve().parent.parent
    config_dir = (
        repo_root / "yosai_intel_dashboard" / "src" / "infrastructure" / "config"
    )

    package_name = "_temp_config"
    pkg = ModuleType(package_name)
    pkg.__path__ = [str(config_dir)]
    sys.modules[package_name] = pkg

    import optional_dependencies

    optional_dependencies._fallbacks.pop("cryptography.fernet", None)
    optional_dependencies._fallbacks.pop("cryptography", None)

    # Stub minimal dependencies to avoid heavy imports
    core_exc = ModuleType("yosai_intel_dashboard.src.core.exceptions")

    class ConfigurationError(Exception):
        pass

    core_exc.ConfigurationError = ConfigurationError
    sys.modules["yosai_intel_dashboard.src.core.exceptions"] = core_exc

    dynamic = ModuleType(f"{package_name}.dynamic_config")

    class _DummyDynamicConfig:
        @staticmethod
        def get_db_connection_timeout() -> int:
            return 1

        @staticmethod
        def get_db_pool_size() -> int:
            return 1

    dynamic.dynamic_config = _DummyDynamicConfig()
    sys.modules[f"{package_name}.dynamic_config"] = dynamic

    spec = importlib.util.spec_from_file_location(
        f"{package_name}.base",
        config_dir / "base.py",
        submodule_search_locations=[str(config_dir)],
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None  # for type checkers
    spec.loader.exec_module(module)
    return module.DatabaseConfig


DatabaseConfig = _load_database_config()
TEST_PASSWORD = os.environ.get("DB_PASSWORD", os.urandom(16).hex())


def test_database_config_round_trip():
    cfg = DatabaseConfig(
        type="postgresql",
        host="db",
        port=5432,
        name="test",
        user="u",
        password=TEST_PASSWORD,
    )
    cfg_dict = cfg.to_dict()
    new_cfg = DatabaseConfig.from_dict(cfg_dict)
    assert new_cfg == cfg


def test_database_config_exclude_password():
    cfg = DatabaseConfig(password=TEST_PASSWORD)
    cfg_dict = cfg.to_dict(include_password=False)
    assert "password" not in cfg_dict
    new_cfg = DatabaseConfig.from_dict(cfg_dict)
    assert new_cfg.password == ""


def test_database_config_encrypt_round_trip():
    key = Fernet.generate_key().decode()
    cfg = DatabaseConfig(password=TEST_PASSWORD)
    cfg_dict = cfg.to_dict(fernet_key=key)
    new_cfg = DatabaseConfig.from_dict(cfg_dict, fernet_key=key)
    assert new_cfg == cfg
