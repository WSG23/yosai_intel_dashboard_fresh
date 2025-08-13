"""Compatibility wrapper for tests.

The test-suite expects the analytics microservice to be importable from the
``services`` package.  The actual implementation lives in
``yosai_intel_dashboard.src.services.analytics_microservice``.  This module
re-exports the FastAPI ``app`` object from the real implementation so that both
import locations behave the same.
"""

from yosai_intel_dashboard.src.services.analytics_microservice.app import app

__all__ = ["app"]
