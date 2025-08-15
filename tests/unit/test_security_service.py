import pytest

import tests.config  # noqa: F401  # trigger environment setup
import os
import importlib.util
import types
import sys
from pathlib import Path

import pytest
os.environ.setdefault("CACHE_TTL_SECONDS", "1")
os.environ.setdefault("JWKS_CACHE_TTL", "1")
from yosai_intel_dashboard.src.core.imports.resolver import safe_import

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
    assert result.valid is False
    assert "invalid_filename" in (result.issues or [])


def test_oversized_upload_is_invalid():
    validator = SecurityValidator()
    too_big = dynamic_config.security.max_upload_mb * 1024 * 1024 + 1
    result = validator.validate_file_meta("big.csv", b"x" * too_big)
    assert result.valid is False
    assert "file_too_large" in (result.issues or [])


def test_sanitize_filename_rejects_path_components():
    validator = SecurityValidator()
    result = validator.sanitize_filename("../foo/bar.csv")
    assert result.valid is False
    assert "invalid_filename" in (result.issues or [])


def test_valid_png_signature():
    validator = SecurityValidator()
    png = b"\x89PNG\r\n\x1a\nrest"
    result = validator.validate_file_meta("img.png", png)
    assert result.valid


def test_signature_mismatch_detected():
    validator = SecurityValidator()
    png = b"\x89PNG\r\n\x1a\nrest"
    result = validator.validate_file_meta("img.jpg", png)
    assert result.valid is False
    assert "file_signature_mismatch" in (result.issues or [])


def test_virus_scan_failure():
    class BadScanner(SecurityValidator):
        def _virus_scan(self, content: bytes) -> None:
            raise ValidationError("virus")

    validator = BadScanner()
    png = b"\x89PNG\r\n\x1a\nrest"
    result = validator.validate_file_meta("img.png", png)
    assert result.valid is False
    assert "virus_detected" in (result.issues or [])
