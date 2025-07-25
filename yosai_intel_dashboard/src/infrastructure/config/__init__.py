"""Infrastructure configuration utilities."""

# Intentionally avoid eager imports to prevent circular dependencies during
# package initialization. Attributes are imported on first access.

__all__ = [
    "DatabaseError",
    "ConnectionRetryExhausted",
    "ConnectionValidationFailed",
    "UnicodeEncodingError",
    "execute_secure_query",
]

from importlib import import_module
from pathlib import Path

# Allow importing modules from the legacy top-level ``config`` package.
__path__.append(str(Path(__file__).resolve().parents[4] / "config"))


def __getattr__(name: str) -> object:
    if name in {
        "DatabaseError",
        "ConnectionRetryExhausted",
        "ConnectionValidationFailed",
        "UnicodeEncodingError",
    }:
        module = import_module(f"{__name__}.database_exceptions")
        return getattr(module, name)
    if name == "execute_secure_query":
        module = import_module(f"{__name__}.secure_db")
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
