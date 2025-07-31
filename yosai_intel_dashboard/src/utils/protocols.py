from __future__ import annotations

from typing import Protocol


class SafeDecoderProtocol(Protocol):
    """Callable signature for safe decoding helpers."""

    def __call__(self, data: bytes, encoding: str) -> str: ...


__all__ = ["SafeDecoderProtocol"]
