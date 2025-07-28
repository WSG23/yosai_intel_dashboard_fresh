"""Central analytics utilities and convenience helpers.

This module exposes :func:`create_manager` which instantiates a
``CentralizedAnalyticsManager`` wired with the default stub services used
throughout the tests and documentation.
"""

# ``CentralizedAnalyticsManager`` is imported lazily inside ``create_manager`` to
# avoid circular imports when ``analytics.core`` is imported from submodules.

__all__ = ["CentralizedAnalyticsManager", "create_manager"]


def create_manager():
    """Create a :class:`CentralizedAnalyticsManager` with default services.

    Services are imported within the function body so that importing this module
    does not trigger any heavy imports or circular dependencies.
    """

    # Local imports to prevent circular dependencies
    from .centralized_analytics_manager import CentralizedAnalyticsManager
    from .services import (
        CoreAnalyticsService,
        AIAnalyticsService,
        PerformanceAnalyticsService,
        DataProcessingService,
    )

    return CentralizedAnalyticsManager(
        core_service=CoreAnalyticsService(),
        ai_service=AIAnalyticsService(),
        performance_service=PerformanceAnalyticsService(),
        data_service=DataProcessingService(),
    )


