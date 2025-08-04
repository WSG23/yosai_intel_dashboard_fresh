"""Container bootstrap utilities."""
from __future__ import annotations

import logging

from yosai_intel_dashboard.src.infrastructure.di.service_container import ServiceContainer
from startup.registry_startup import register_optional_services
from startup.service_registration import register_all_application_services
from yosai_intel_dashboard.src.infrastructure.config.common_indexes import COMMON_INDEXES
from yosai_intel_dashboard.src.database.index_optimizer import IndexOptimizer

logger = logging.getLogger(__name__)


def bootstrap_container() -> ServiceContainer:
    """Create and configure a :class:`ServiceContainer`."""
    container = ServiceContainer()
    register_all_application_services(container)
    register_optional_services()

    # Ensure common indexes exist. Failures are logged but do not prevent
    # startup since this is a best-effort optimization.
    try:
        optimizer = IndexOptimizer()
        for table, column_sets in COMMON_INDEXES.items():
            for cols in column_sets:
                optimizer.apply_recommendations(table, cols)
    except Exception as exc:  # pragma: no cover - best effort
        logger.warning("Failed to apply common index recommendations: %s", exc)

    return container

__all__ = ["bootstrap_container"]
