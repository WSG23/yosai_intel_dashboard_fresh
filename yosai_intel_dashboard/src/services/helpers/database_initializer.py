from __future__ import annotations

import logging
from typing import Any, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - for type checking only
    from yosai_intel_dashboard.src.core.interfaces.service_protocols import (
        DatabaseAnalyticsRetrieverProtocol,
    )
    from yosai_intel_dashboard.src.infrastructure.config.database_manager import (
        DatabaseConnectionFactory,
        DatabaseSettings,
    )
    from yosai_intel_dashboard.src.infrastructure.config.database_exceptions import (
        DatabaseError,
    )
    from yosai_intel_dashboard.src.services.db_analytics_helper import (
        DatabaseAnalyticsHelper,
    )
    from yosai_intel_dashboard.src.services.summary_reporter import SummaryReporter

logger = logging.getLogger(__name__)


def initialize_database(
    database: Any | None,
    *,
    settings: 'DatabaseSettings' | None = None,
    settings_provider: callable | None = None,
) -> Tuple[Optional[Any], 'DatabaseAnalyticsHelper', 'SummaryReporter']:
    """Return initialized database connection and helpers."""
    from yosai_intel_dashboard.src.infrastructure.config.database_exceptions import (
        DatabaseError,
    )
    from yosai_intel_dashboard.src.infrastructure.config.database_manager import (
        DatabaseConnectionFactory,
        DatabaseSettings,
    )
    from yosai_intel_dashboard.src.services.db_analytics_helper import (
        DatabaseAnalyticsHelper,
    )
    from yosai_intel_dashboard.src.services.summary_reporter import SummaryReporter

    try:
        if database is not None:
            db_connection = database
            return (
                db_connection,
                DatabaseAnalyticsHelper(database),
                SummaryReporter(database),
            )

        if settings is None:
            if settings_provider is not None:
                settings = settings_provider()
            else:
                settings = DatabaseSettings()

        factory = DatabaseConnectionFactory(settings)
        db_connection = factory.create()
        logger.info("Database connection initialized")
        return (
            db_connection,
            DatabaseAnalyticsHelper(db_connection),
            SummaryReporter(db_connection),
        )
    except (ImportError, DatabaseError) as exc:
        logger.warning("Database initialization failed: %s", exc)
        return (
            None,
            DatabaseAnalyticsHelper(None),
            SummaryReporter(None),
        )


class DatabaseInitializer:
    """Helper class to initialize database components."""

    def __init__(
        self,
        initializer=initialize_database,
        retriever_factory=None,
    ) -> None:
        self._initializer = initializer
        if retriever_factory is None:
            from yosai_intel_dashboard.src.core.interfaces.service_protocols import (
                get_database_analytics_retriever,
            )

            self._retriever_factory = get_database_analytics_retriever
        else:
            self._retriever_factory = retriever_factory

    def setup(
        self,
        database: Any | None,
        db_retriever: DatabaseAnalyticsRetrieverProtocol | None = None,
    ) -> Tuple[Optional[Any], DatabaseAnalyticsHelper, SummaryReporter, 'DatabaseAnalyticsRetrieverProtocol']:
        """Return database connection, helpers and retriever."""

        db_manager, helper, reporter = self._initializer(database)
        retriever = db_retriever or self._retriever_factory(helper)
        return db_manager, helper, reporter, retriever


__all__ = ["initialize_database", "DatabaseInitializer"]
