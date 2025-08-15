"""Unified analytics service package.

This package consolidates the previous ``analytics`` and
``analytics_microservice`` modules.  It re-exports the FastAPI
application and helper utilities from the real implementation in
``yosai_intel_dashboard``.  The package also exposes a small CLI entry
point via :mod:`services.analytics.cli`.
"""

__all__ = ["app", "analytics_service", "async_queries", "model_loader"]
