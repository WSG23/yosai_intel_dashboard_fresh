"""Expose API routes used by the dashboard."""

from . import plugin_performance  # noqa: F401
from . import risk_scoring  # noqa: F401

__all__ = ["plugin_performance", "risk_scoring"]
