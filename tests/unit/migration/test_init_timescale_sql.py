import pathlib

SQL_PATH = pathlib.Path("scripts/init_timescaledb.sql")


def _read_sql() -> str:
    return SQL_PATH.read_text().lower()


def test_hypertable_and_index_creation() -> None:
    sql = _read_sql()
    assert "create_hypertable('access_events'" in sql
    assert "chunk_time_interval" in sql
    # primary key index ensures index creation
    assert "primary key" in sql


def test_compression_and_retention_policies() -> None:
    sql = _read_sql()
    assert "add_compression_policy" in sql
    assert "add_retention_policy" in sql
