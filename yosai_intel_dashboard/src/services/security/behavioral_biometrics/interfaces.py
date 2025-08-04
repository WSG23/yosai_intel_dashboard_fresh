"""Interfaces for behavioral biometric data collection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Protocol


@dataclass
class KeystrokeEvent:
    """A single keystroke event with timestamps for analysis."""

    key: str
    press_time: float
    release_time: float


class KeystrokeCollector(Protocol):
    """Protocol for classes that collect keystroke events."""

    def collect(self) -> Iterable[KeystrokeEvent]:
        """Return an iterable of :class:`KeystrokeEvent` instances."""
        ...


class GaitCollector(Protocol):
    """Protocol for classes that capture gait sequences."""

    def collect(self) -> Iterable[float]:
        """Return a sequence of gait measurements."""
        ...
