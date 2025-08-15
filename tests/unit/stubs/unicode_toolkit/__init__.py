"""Stub unicode_toolkit module for tests."""

from __future__ import annotations

from typing import Any, Iterable, Mapping


def safe_encode_text(value: Any) -> str:
    if isinstance(value, bytes):
        value = value.decode("utf-8", "surrogatepass")
    # Normalize surrogate pairs and drop unpaired surrogates
    return value.encode("utf-16", "surrogatepass").decode("utf-16", "ignore")


class UnicodeHandler:
    @staticmethod
    def sanitize(obj: Any) -> Any:
        if isinstance(obj, (str, bytes, bytearray)):
            return safe_encode_text(obj)
        if isinstance(obj, Mapping):
            return {k: UnicodeHandler.sanitize(v) for k, v in obj.items()}
        if isinstance(obj, Iterable) and not isinstance(obj, (bytes, bytearray)):
            return type(obj)(UnicodeHandler.sanitize(v) for v in obj)
        return obj


__all__ = ["safe_encode_text", "UnicodeHandler"]

