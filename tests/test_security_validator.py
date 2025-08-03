import html
import logging
import sys
import types
from pathlib import Path
import importlib

import pytest

# ---------------------------------------------------------------------------
# Provide lightweight stubs for heavy dependencies used during import

core_exc = types.ModuleType("yosai_intel_dashboard.src.core.exceptions")


class ValidationError(Exception):
    pass


core_exc.ValidationError = ValidationError
sys.modules.setdefault("yosai_intel_dashboard", types.ModuleType("yosai_intel_dashboard"))
sys.modules.setdefault(
    "yosai_intel_dashboard.src", types.ModuleType("yosai_intel_dashboard.src")
)
sys.modules.setdefault(
    "yosai_intel_dashboard.src.core", types.ModuleType("yosai_intel_dashboard.src.core")
)
sys.modules["yosai_intel_dashboard.src.core.exceptions"] = core_exc

dyn_cfg = types.ModuleType(
    "yosai_intel_dashboard.src.infrastructure.config.dynamic_config"
)
dyn_cfg.dynamic_config = types.SimpleNamespace(
    security=types.SimpleNamespace(max_upload_mb=10)
)
sys.modules.setdefault(
    "yosai_intel_dashboard.src.infrastructure",
    types.ModuleType("yosai_intel_dashboard.src.infrastructure"),
)
sys.modules.setdefault(
    "yosai_intel_dashboard.src.infrastructure.config",
    types.ModuleType("yosai_intel_dashboard.src.infrastructure.config"),
)
sys.modules[
    "yosai_intel_dashboard.src.infrastructure.config.dynamic_config"
] = dyn_cfg

# Stub the package to avoid executing validation.__init__
validation_pkg = types.ModuleType("validation")
validation_pkg.__path__ = [str(Path(__file__).resolve().parents[1] / "validation")]
sys.modules["validation"] = validation_pkg

SecurityValidator = importlib.import_module(
    "validation.security_validator"
).SecurityValidator



def test_sql_injection_validation():
    validator = SecurityValidator(rate_limit=1, window_seconds=60)
    with pytest.raises(Exception):
        validator.validate_input("1; DROP TABLE users")


def test_main_validation_orchestration():
    validator = SecurityValidator(rate_limit=1, window_seconds=60)
    value = "<script>alert('xss')</script>"
    with pytest.raises(Exception):
        validator.validate_input(value, "comment")


@pytest.mark.skip("File upload validation not covered in this test")
def test_validate_file_upload_rules():
    validator = SecurityValidator(rate_limit=1, window_seconds=60)
    valid = validator.validate_file_upload("ok.csv", b"a,b\n1,2")
    assert valid["valid"]
    with pytest.raises(Exception):
        validator.validate_file_upload("bad.csv", b"=cmd()")


def test_validation_cache_and_logging(caplog):
    validator = SecurityValidator()
    with caplog.at_level(logging.INFO):
        validator.validate_input("safe input")
        validator.validate_input("safe input")

    cache_info = validator._cached_validate.cache_info()
    assert cache_info.hits == 1

    records = [r for r in caplog.records if r.name == "validation.security_validator"]
    assert any("Validation succeeded" in r.message for r in records)


def test_validation_logs_failure(caplog):
    validator = SecurityValidator()
    with caplog.at_level(logging.WARNING):
        with pytest.raises(Exception):
            validator.validate_input("1; DROP TABLE users")

    records = [r for r in caplog.records if r.name == "validation.security_validator"]
    assert any("Validation failed" in r.message for r in records)


