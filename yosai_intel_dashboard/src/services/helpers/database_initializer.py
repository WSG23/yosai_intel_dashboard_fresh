import logging
from typing import Any, Optional, Tuple

from config.database_exceptions import DatabaseError
from yosai_intel_dashboard.src.services.db_analytics_helper import DatabaseAnalyticsHelper
from yosai_intel_dashboard.src.services.summary_reporter import SummaryReporter

logger = logging.getLogger(__name__)


def initialize_database(
    database: Any | None,
) -> Tuple[Optional[Any], DatabaseAnalyticsHelper, SummaryReporter]:
    """Return initialized database manager and helpers."""
    try:
        if database is not None:
            database_manager = database
            return (
                database_manager,
                DatabaseAnalyticsHelper(database),
                SummaryReporter(database),
            )

        from config import get_database_config
        from config.database_manager import (
            DatabaseManager,
        )
        from config.database_manager import DatabaseSettings as ManagerConfig

        cfg = get_database_config()
        manager_cfg = ManagerConfig(
            type=cfg.type,
            host=cfg.host,
            port=cfg.port,
            name=cfg.name,
            user=cfg.user,
            password=cfg.password,
        )
        database_manager = DatabaseManager(manager_cfg)
        logger.info("Database manager initialized")
        return (
            database_manager,
            DatabaseAnalyticsHelper(database_manager),
            SummaryReporter(database_manager),
        )
    except (ImportError, DatabaseError) as exc:
        logger.warning("Database initialization failed: %s", exc)
        return (
            None,
            DatabaseAnalyticsHelper(None),
            SummaryReporter(None),
        )


__all__ = ["initialize_database"]
