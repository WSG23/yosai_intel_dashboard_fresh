from __future__ import annotations

import pytest

from yosai_intel_dashboard.src.database.utils import parse_connection_string


def test_parse_postgres():
    info = parse_connection_string("postgresql://user:pass@localhost:5432/db")
    assert info.dialect == "postgresql"
    assert info.user == "user"
    assert info.password == "pass"
    assert info.host == "localhost"
    assert info.port == 5432
    assert info.database == "db"
    assert info.build_url() == "postgresql://user:pass@localhost:5432/db"


def test_parse_sqlite():
    info = parse_connection_string("sqlite:///tmp/test.db")
    assert info.dialect == "sqlite"
    assert info.path == "/tmp/test.db"
    assert info.build_url() == "sqlite:///tmp/test.db"


def test_invalid_scheme():
    with pytest.raises(ValueError):
        parse_connection_string("mysql://user:pass@localhost/db")


def test_postgres_missing_db():
    with pytest.raises(ValueError):
        parse_connection_string("postgresql://user:pass@localhost")


def test_build_asyncpg_url():
    info = parse_connection_string("postgresql://user@localhost/db")
    async_url = info.build_url("postgresql+asyncpg")
    assert async_url == "postgresql+asyncpg://user@localhost:5432/db"
