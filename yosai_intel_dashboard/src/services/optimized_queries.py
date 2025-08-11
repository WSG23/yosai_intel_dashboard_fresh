from __future__ import annotations

"""Optimized database query helpers."""

from typing import Any, Dict, Iterable, List, Sequence

from infrastructure.security.query_builder import SecureQueryBuilder
from yosai_intel_dashboard.src.database.secure_exec import (
    execute_query,
    execute_secure_query,
)
from yosai_intel_dashboard.src.database.types import DatabaseConnection


class OptimizedQueryService:
    """Provide optimized queries for fetching events and users."""

    def __init__(self, db: DatabaseConnection) -> None:
        self.db = db

    # ------------------------------------------------------------------
    def get_events_with_users(self, facility_id: str) -> List[Dict[str, Any]]:
        """Return events joined with user info for a facility."""
        query = """
            SELECT ae.*, p.*
            FROM access_events ae
            JOIN doors d ON ae.door_id = d.door_id
            JOIN people p ON ae.person_id = p.person_id
            WHERE d.facility_id = %s
            ORDER BY ae.timestamp DESC
        """
        params = (facility_id,)
        rows = execute_secure_query(self.db, query, params)
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    def batch_get_users(self, user_ids: Sequence[str]) -> List[Dict[str, Any]]:
        """Fetch multiple users in a single query."""
        if not user_ids:
            return []

        query = "SELECT * FROM people WHERE person_id = ANY(%s)"
        params = (list(user_ids),)
        try:
            rows = execute_secure_query(self.db, query, params)
        except Exception:  # Fallback for databases without ANY()
            builder = SecureQueryBuilder(
                allowed_tables={"people"}, allowed_columns={"person_id"}
            )
            table = builder.table("people")
            column = builder.column("person_id")
            placeholders = ", ".join("%s" for _ in user_ids)
            query_str = f"SELECT * FROM {table} WHERE {column} IN ({placeholders})"
            query, params = builder.build(query_str, tuple(user_ids))
            rows = execute_secure_query(self.db, query, params)

        return [dict(r) for r in rows]


__all__ = ["OptimizedQueryService"]
