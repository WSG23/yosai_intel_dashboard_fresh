"""Prometheus metric definitions used across monitoring modules.

Import from this package to register counters and gauges that expose
application health and performance data.
"""

from .breaker import circuit_breaker_state

__all__ = ["circuit_breaker_state"]
