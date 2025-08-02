"""Deprecated legacy_auth module."""
from importlib import util
from pathlib import Path

spec = util.spec_from_file_location(
    "utils.deprecation",
    Path(__file__).resolve().parents[1]
    / "yosai_intel_dashboard"
    / "src"
    / "utils"
    / "deprecation.py",
)
module = util.module_from_spec(spec)
assert spec and spec.loader  # for mypy
spec.loader.exec_module(module)  # type: ignore[assignment]
module.warn("legacy-auth")
