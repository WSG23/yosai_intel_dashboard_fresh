from __future__ import annotations

"""Optimized database query helpers."""

from typing import Any, Dict, Iterable, List, Sequence

from database.types import DatabaseConnection


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
        rows = self.db.execute_query(query, (facility_id,))
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    def batch_get_users(self, user_ids: Sequence[str]) -> List[Dict[str, Any]]:
        """Fetch multiple users in a single query."""
        if not user_ids:
            return []

        query = "SELECT * FROM people WHERE person_id = ANY(%s)"
        try:
            rows = self.db.execute_query(query, (list(user_ids),))
        except Exception:  # Fallback for databases without ANY()
            placeholders = ",".join(["%s"] * len(user_ids))
            query = f"SELECT * FROM people WHERE person_id IN ({placeholders})"
            rows = self.db.execute_query(query, tuple(user_ids))

        return [dict(r) for r in rows]


__all__ = ["OptimizedQueryService"]
