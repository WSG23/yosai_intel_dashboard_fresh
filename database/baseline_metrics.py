from __future__ import annotations

"""Utilities for storing and retrieving baseline metrics.

This module provides :class:`BaselineMetricsDB` which offers a simple
interface for persisting baseline metrics in a relational database.
Applications can use ``update_baseline`` and ``get_baseline`` to manage
historical performance metrics.
"""

import logging
from typing import Dict, List

from database.connection import create_database_connection
from database.secure_exec import execute_command

logger = logging.getLogger(__name__)


class BaselineMetricsDB:
    """Lightweight storage for historical baseline metrics."""

    def __init__(self, table_name: str = "behavior_baselines") -> None:
        self.conn = create_database_connection()
        self.table_name = table_name
        self._ensure_table()

    # ------------------------------------------------------------------
    def _ensure_table(self) -> None:
        execute_command(
            self.conn,
            f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                entity_type VARCHAR(10) NOT NULL,
                entity_id VARCHAR(50) NOT NULL,
                metric VARCHAR(50) NOT NULL,
                value FLOAT NOT NULL,
                PRIMARY KEY (entity_type, entity_id, metric)
            )
            """,
        )

    # ------------------------------------------------------------------
    def update_baseline(
        self, entity_type: str, entity_id: str, metrics: Dict[str, float]
    ) -> None:
        for metric, value in metrics.items():
            try:
                execute_command(
                    self.conn,
                    f"""
                    INSERT INTO {self.table_name} (entity_type, entity_id, metric, value)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(entity_type, entity_id, metric)
                    DO UPDATE SET value = excluded.value
                    """,
                    (entity_type, entity_id, metric, float(value)),
                )
            except Exception as exc:  # pragma: no cover - log and continue
                logger.warning("Failed to store baseline metric: %s", exc)

    # ------------------------------------------------------------------
    def get_baseline(self, entity_type: str, entity_id: str) -> Dict[str, float]:
        try:
            rows: List[Dict] = execute_query(
                self.conn,
                f"SELECT metric, value FROM {self.table_name} WHERE entity_type=? AND entity_id=?",
                (entity_type, entity_id),
            )
            return {row["metric"]: float(row["value"]) for row in rows}
        except Exception as exc:  # pragma: no cover - log and continue
            logger.warning("Failed to fetch baseline metrics: %s", exc)
            return {}
