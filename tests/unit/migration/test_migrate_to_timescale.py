from __future__ import annotations

from typing import Any, Dict, List

import pytest

from scripts.migrate_to_timescale import (
    get_checkpoint,
    rows_checksum,
    update_checkpoint,
    validate_chunk,
)


class DummyCursor:
    def __init__(self) -> None:
        self.checkpoints: Dict[str, int] = {}
        self.rows: List[dict[str, Any]] = []
        self.result: List[Any] = []
        self.last_query: str | None = None
        self.last_params: tuple | None = None

    def execute(self, query: str, params: tuple | None = None) -> None:
        params = params or ()
        self.last_query = query
        self.last_params = params
        q = query.lower().strip()
        if q.startswith("select last_id"):
            table = params[0]
            if table in self.checkpoints:
                self.result = [(self.checkpoints[table],)]
            else:
                self.result = []
        elif q.startswith("insert into"):
            table, last_id = params
            self.checkpoints[table] = last_id
            self.result = []
        elif q.startswith("select *"):
            start, end = params
            self.result = [r for r in self.rows if start < r["id"] <= end]
        else:
            self.result = []

    def fetchone(self) -> Any:
        return self.result[0] if self.result else None

    def fetchall(self) -> List[Any]:
        return list(self.result)


def test_checkpoint_roundtrip() -> None:
    cur = DummyCursor()
    update_checkpoint(cur, "access_events", 42)
    assert get_checkpoint(cur, "access_events") == 42


def test_validate_chunk_passes() -> None:
    cur = DummyCursor()
    cur.rows = [{"id": 1, "val": "a"}, {"id": 2, "val": "b"}]
    checksum = rows_checksum(cur.rows)
    validate_chunk(cur, "tbl", 0, 2, checksum, 2)


def test_validate_chunk_failure() -> None:
    cur = DummyCursor()
    cur.rows = [{"id": 1, "val": "a"}]
    checksum = rows_checksum(cur.rows)
    with pytest.raises(ValueError):
        validate_chunk(cur, "tbl", 0, 2, checksum, 2)


def test_update_checkpoint_uses_parameters() -> None:
    cur = DummyCursor()
    malicious = "tbl'; DROP TABLE x; --"
    update_checkpoint(cur, malicious, 5)
    assert malicious not in (cur.last_query or "")
    assert cur.last_params == (malicious, 5)
