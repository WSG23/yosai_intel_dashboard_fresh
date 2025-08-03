import pytest

import tests.config  # noqa: F401  # trigger environment setup
import os
import importlib.util
import types
import sys
from pathlib import Path

os.environ.setdefault("CACHE_TTL_SECONDS", "1")
os.environ.setdefault("JWKS_CACHE_TTL", "1")
from tests.import_helpers import safe_import, import_optional

validation_path = Path(__file__).resolve().parents[1] / "validation"
pkg = types.ModuleType("validation")
pkg.__path__ = [str(validation_path)]
sys.modules.setdefault("validation", pkg)

# Stub core exceptions to avoid heavy imports
exceptions = types.ModuleType("yosai_intel_dashboard.src.core.exceptions")
class ValidationError(Exception):
    pass
exceptions.ValidationError = ValidationError
sys.modules["yosai_intel_dashboard.src.core.exceptions"] = exceptions

# Stub dynamic_config used by SecurityValidator
cfg_module = types.ModuleType(
    "yosai_intel_dashboard.src.infrastructure.config.dynamic_config"
)
cfg_module.dynamic_config = types.SimpleNamespace(
    security=types.SimpleNamespace(max_upload_mb=1)
)
sys.modules[
    "yosai_intel_dashboard.src.infrastructure.config.dynamic_config"
] = cfg_module

spec = importlib.util.spec_from_file_location(
    "validation.security_validator", validation_path / "security_validator.py"
)
module = importlib.util.module_from_spec(spec)
sys.modules["validation.security_validator"] = module
spec.loader.exec_module(module)

SecurityValidator = module.SecurityValidator
ValidationError = exceptions.ValidationError
dynamic_config = cfg_module.dynamic_config


def test_malicious_filename_is_invalid():
    validator = SecurityValidator()
    result = validator.validate_file_meta("../../evil.csv", b"data")
    assert result["valid"] is False
    assert any("Invalid filename" in issue for issue in result["issues"])


def test_oversized_upload_is_invalid():
    validator = SecurityValidator()
    too_big = dynamic_config.security.max_upload_mb * 1024 * 1024 + 1
    result = validator.validate_file_meta("big.csv", b"x" * too_big)
    assert result["valid"] is False
    assert any("File too large" in issue for issue in result["issues"])


def test_sanitize_filename_rejects_path_components():
    validator = SecurityValidator()
    with pytest.raises(ValidationError):
        validator.sanitize_filename("../foo/bar.csv")


def test_valid_png_signature():
    validator = SecurityValidator()
    png = b"\x89PNG\r\n\x1a\nrest"
    result = validator.validate_file_meta("img.png", png)
    assert result["valid"]


def test_signature_mismatch_raises():
    validator = SecurityValidator()
    png = b"\x89PNG\r\n\x1a\nrest"
    with pytest.raises(ValidationError):
        validator.validate_file_meta("img.jpg", png)


def test_virus_scan_failure():
    class BadScanner(SecurityValidator):
        def _virus_scan(self, content: bytes) -> None:
            raise ValidationError("virus")

    validator = BadScanner()
    png = b"\x89PNG\r\n\x1a\nrest"
    with pytest.raises(ValidationError):
        validator.validate_file_meta("img.png", png)
