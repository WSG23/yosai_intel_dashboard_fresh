import logging
from typing import Any, Optional, Tuple

from yosai_intel_dashboard.src.infrastructure.config.database_exceptions import DatabaseError
from yosai_intel_dashboard.src.infrastructure.config.database_manager import (
    DatabaseConnectionFactory,
    DatabaseSettings,
)
from yosai_intel_dashboard.src.services.db_analytics_helper import DatabaseAnalyticsHelper
from yosai_intel_dashboard.src.services.summary_reporter import SummaryReporter

logger = logging.getLogger(__name__)


def initialize_database(
    database: Any | None,
    *,
    settings: DatabaseSettings | None = None,
    settings_provider: callable | None = None,
) -> Tuple[Optional[Any], DatabaseAnalyticsHelper, SummaryReporter]:
    """Return initialized database connection and helpers."""
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


__all__ = ["initialize_database"]
