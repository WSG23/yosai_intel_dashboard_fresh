from datetime import datetime
from unittest.mock import MagicMock

import scripts.migrate_to_timescale as mts


def test_migrate_table_small_dataset(monkeypatch):
    source_rows = [
        {"id": 1, "time": datetime(2024, 1, 1), "val": "a"},
        {"id": 2, "time": datetime(2024, 1, 2), "val": "b"},
    ]
    fetch_calls = []

    def fetch_chunk_mock(cur, table, start, size):
        fetch_calls.append((start, size))
        return source_rows if start == 0 else []

    inserted = []

    def insert_rows_mock(cur, table, rows):
        inserted.extend(rows)

    monkeypatch.setattr(mts, "fetch_chunk", fetch_chunk_mock)
    monkeypatch.setattr(mts, "insert_rows", insert_rows_mock)
    monkeypatch.setattr(mts, "validate_chunk", lambda *a, **k: None)
    monkeypatch.setattr(mts, "update_checkpoint", lambda *a, **k: None)

    src_conn = MagicMock()
    tgt_conn = MagicMock()
    src_cur = MagicMock()
    tgt_cur = MagicMock()
    src_cur.fetchone.return_value = (len(source_rows),)
    src_conn.cursor.return_value.__enter__.return_value = src_cur
    src_conn.cursor.return_value.__exit__.return_value = None
    tgt_conn.cursor.return_value.__enter__.return_value = tgt_cur
    tgt_conn.cursor.return_value.__exit__.return_value = None

    mts.migrate_table(src_conn, tgt_conn, "access_events")

    assert inserted == source_rows
    assert fetch_calls == [(0, mts.CHUNK_SIZE), (2, mts.CHUNK_SIZE)]
    tgt_conn.commit.assert_called_once()
