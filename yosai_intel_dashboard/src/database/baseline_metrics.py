from __future__ import annotations

"""Utilities for storing and retrieving baseline metrics.

This module provides :class:`BaselineMetricsDB` which offers a simple
interface for persisting baseline metrics in a relational database.
Applications can use ``update_baseline`` and ``get_baseline`` to manage
historical performance metrics.
"""

import logging
from typing import Dict

from infrastructure.security.query_builder import SecureQueryBuilder
from yosai_intel_dashboard.src.database.connection import create_database_connection
from yosai_intel_dashboard.src.database.types import DBRows
from yosai_intel_dashboard.src.infrastructure.security.secure_query_wrapper import (
    execute_secure_command,
    execute_secure_sql,
)

logger = logging.getLogger(__name__)


class BaselineMetricsDB:
    """Lightweight storage for historical baseline metrics."""

    def __init__(self, table_name: str = "behavior_baselines") -> None:
        self.conn = create_database_connection()
        self.table_name = table_name
        # Validate table name against allow-list
        self.builder = SecureQueryBuilder(allowed_tables={self.table_name})
        self._ensure_table()

    # ------------------------------------------------------------------
    def _ensure_table(self) -> None:
        table = self.builder.table(self.table_name)
        create_sql = (
            """
            CREATE TABLE IF NOT EXISTS {table} (
                entity_type VARCHAR(10) NOT NULL,
                entity_id VARCHAR(50) NOT NULL,
                metric VARCHAR(50) NOT NULL,
                value FLOAT NOT NULL,
                PRIMARY KEY (entity_type, entity_id, metric)
            )
            """
        ).replace("{table}", table)
        execute_secure_command(self.conn, create_sql)

    # ------------------------------------------------------------------
    def update_baseline(
        self, entity_type: str, entity_id: str, metrics: Dict[str, float]
    ) -> None:
        for metric, value in metrics.items():
            try:
                table = self.builder.table(self.table_name)
                insert_sql = (
                    """
                    INSERT INTO {table} (entity_type, entity_id, metric, value)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(entity_type, entity_id, metric)
                    DO UPDATE SET value = excluded.value
                    """
                ).replace("{table}", table)
                execute_secure_command(
                    self.conn,
                    insert_sql,
                    (entity_type, entity_id, metric, float(value)),
                )
            except Exception as exc:  # pragma: no cover - log and continue
                logger.warning("Failed to store baseline metric: %s", exc)

    # ------------------------------------------------------------------
    def get_baseline(self, entity_type: str, entity_id: str) -> Dict[str, float]:
        try:
            table = self.builder.table(self.table_name)
            select_sql = (
                "SELECT metric, value FROM {table} WHERE entity_type=? AND entity_id=?"
            ).replace("{table}", table)
            sql, params = self.builder.build(
                select_sql, (entity_type, entity_id), logger=logger
            )
            rows: DBRows = execute_secure_sql(self.conn, sql, params)
            return {row["metric"]: float(row["value"]) for row in rows}
        except Exception as exc:  # pragma: no cover - log and continue
            logger.warning("Failed to fetch baseline metrics: %s", exc)
            return {}
