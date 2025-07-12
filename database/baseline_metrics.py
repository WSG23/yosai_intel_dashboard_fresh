from __future__ import annotations

import logging
from typing import Dict, List

from database.connection import create_database_connection

logger = logging.getLogger(__name__)


class BaselineMetricsDB:
    """Lightweight storage for historical baseline metrics."""

    def __init__(self, table_name: str = "behavior_baselines") -> None:
        self.conn = create_database_connection()
        self.table_name = table_name
        self._ensure_table()

    # ------------------------------------------------------------------
    def _ensure_table(self) -> None:
        self.conn.execute_command(
            f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                entity_type VARCHAR(10) NOT NULL,
                entity_id VARCHAR(50) NOT NULL,
                metric VARCHAR(50) NOT NULL,
                value FLOAT NOT NULL,
                PRIMARY KEY (entity_type, entity_id, metric)
            )
            """
        )

    # ------------------------------------------------------------------
    def update_baseline(
        self, entity_type: str, entity_id: str, metrics: Dict[str, float]
    ) -> None:
        for metric, value in metrics.items():
            try:
                self.conn.execute_command(
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
            rows: List[Dict] = self.conn.execute_query(
                f"SELECT metric, value FROM {self.table_name} WHERE entity_type=? AND entity_id=?",
                (entity_type, entity_id),
            )
            return {row["metric"]: float(row["value"]) for row in rows}
        except Exception as exc:  # pragma: no cover - log and continue
            logger.warning("Failed to fetch baseline metrics: %s", exc)
            return {}
