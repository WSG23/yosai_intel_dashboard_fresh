import base64
import importlib.util
import sys
import types
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import pandas as pd
import pytest


def _load_process_uploaded_file():
    """Dynamically load ``process_uploaded_file`` with minimal stubs."""
    # Stub protocol modules used during import
    core_interfaces = types.ModuleType(
        "yosai_intel_dashboard.src.core.interfaces.protocols"
    )
    class FileProcessorProtocol(Protocol):
        ...
    core_interfaces.FileProcessorProtocol = FileProcessorProtocol
    sys.modules[
        "yosai_intel_dashboard.src.core.interfaces.protocols"
    ] = core_interfaces

    core_proto = types.ModuleType("yosai_intel_dashboard.src.core.protocols")
    class ConfigurationProtocol(Protocol):
        ...
    core_proto.ConfigurationProtocol = ConfigurationProtocol
    sys.modules["yosai_intel_dashboard.src.core.protocols"] = core_proto

    # Provide a minimal config module used by file helpers
    core_config = types.ModuleType("yosai_intel_dashboard.src.core.config")
    core_config.get_max_display_rows = lambda: 100
    sys.modules["yosai_intel_dashboard.src.core.config"] = core_config

    # Avoid heavy initialisation of the utils and config packages
    utils_pkg = types.ModuleType("yosai_intel_dashboard.src.utils")
    utils_pkg.__path__ = [
        str(Path(__file__).resolve().parents[2] / "yosai_intel_dashboard" / "src" / "utils")
    ]
    sys.modules["yosai_intel_dashboard.src.utils"] = utils_pkg

    conf_pkg = types.ModuleType("yosai_intel_dashboard.src.infrastructure.config")
    conf_pkg.__path__ = [
        str(
            Path(__file__).resolve().parents[2]
            / "yosai_intel_dashboard"
            / "src"
            / "infrastructure"
            / "config"
        )
    ]
    sys.modules["yosai_intel_dashboard.src.infrastructure.config"] = conf_pkg

    # Stub upload package and ValidationResult dataclass
    upload_pkg = types.ModuleType("yosai_intel_dashboard.src.services.upload")
    upload_pkg.__path__ = []
    sys.modules["yosai_intel_dashboard.src.services.upload"] = upload_pkg

    upload_types_mod = types.ModuleType(
        "yosai_intel_dashboard.src.services.upload.upload_types"
    )
    @dataclass
    class ValidationResult:
        valid: bool
        message: str = ""
    upload_types_mod.ValidationResult = ValidationResult
    sys.modules[
        "yosai_intel_dashboard.src.services.upload.upload_types"
    ] = upload_types_mod

    # Provide a tiny SecurityValidator implementation
    sec_validator = types.ModuleType("validation.security_validator")
    class SecurityValidator:
        def validate_file_meta(self, filename, content):
            return {"valid": True, "filename": Path(filename).name, "issues": []}
        def sanitize_filename(self, filename):
            return Path(filename).name
    sec_validator.SecurityValidator = SecurityValidator
    sys.modules["validation.security_validator"] = sec_validator

    # Stub unicode helper used when logging errors
    unicode_mod = types.ModuleType("unicode_toolkit")
    unicode_mod.safe_encode_text = lambda x: x
    sys.modules["unicode_toolkit"] = unicode_mod

    # Minimal stub for optional ``aiohttp`` dependency
    aiohttp_stub = types.ModuleType("aiohttp")
    class ClientSession: ...
    aiohttp_stub.ClientSession = ClientSession
    sys.modules["aiohttp"] = aiohttp_stub

    # Load the actual module
    module_path = (
        Path(__file__).resolve().parents[2]
        / "yosai_intel_dashboard"
        / "src"
        / "services"
        / "upload"
        / "utils"
        / "file_parser.py"
    )
    spec = importlib.util.spec_from_file_location("file_parser", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    # ``safe_encode_text`` is referenced on error paths
    module.safe_encode_text = lambda x: x
    return module.process_uploaded_file


@pytest.fixture()
def process_uploaded_file():
    return _load_process_uploaded_file()


def _csv_payload(df: pd.DataFrame) -> str:
    csv_bytes = df.to_csv(index=False).encode()
    b64 = base64.b64encode(csv_bytes).decode()
    return f"data:text/csv;base64,{b64}"


def test_process_uploaded_file_success(process_uploaded_file):
    df = pd.DataFrame({"a": [1, 3], "b": [2, 4]})
    payload = _csv_payload(df)
    result = process_uploaded_file(payload, "../../evil.csv")

    assert result["status"] == "success"
    assert result["error"] is None
    assert result["filename"] == "evil.csv"
    pd.testing.assert_frame_equal(result["data"], df)


def test_process_uploaded_file_invalid_base64(process_uploaded_file):
    result = process_uploaded_file("data:text/csv;base64,INVALID", "bad.csv")

    assert result["status"] == "error"
    assert result["data"] is None
    assert result["filename"] == "bad.csv"
    assert result["error"]
