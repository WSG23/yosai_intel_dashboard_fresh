"""Context correlation engine powered by Flink.

This package provides a lightweight Python interface for building and
running Flink jobs that correlate security and environmental event streams
into enriched alerts.  The :class:`ContextEngine` class also exposes a small
pure Python implementation used in tests and when the ``pyflink`` dependency
is not available.
"""

from .engine import ContextEngine, SecurityEvent, EnvironmentalEvent

__all__ = ["ContextEngine", "SecurityEvent", "EnvironmentalEvent"]
