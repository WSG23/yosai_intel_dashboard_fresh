from __future__ import annotations

import sqlite3
import time

import pytest

from yosai_intel_dashboard.src.infrastructure.database.secure_query import (
    SecureQueryBuilder,
)


@pytest.fixture()
def conn():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, password TEXT)"
    )
    conn.execute("INSERT INTO users (name, password) VALUES ('alice', 'secret1')")
    conn.execute("INSERT INTO users (name, password) VALUES ('bob', 'secret2')")
    conn.execute("CREATE TABLE comments (id INTEGER PRIMARY KEY, comment TEXT)")
    conn.commit()
    yield conn
    conn.close()


@pytest.fixture()
def builder():
    return SecureQueryBuilder(
        allowed_tables={"users"},
        allowed_columns={"id", "name", "password"},
    )


def test_classic_injection_blocked(conn, builder):
    payload = "' OR 1=1--"
    unsafe_sql = f"SELECT id FROM users WHERE name = '{payload}'"
    unsafe_rows = conn.execute(unsafe_sql).fetchall()
    assert len(unsafe_rows) == 2

    sql, params = builder.build_select("users", ["id"], {"name": payload})
    rows = conn.execute(sql, params).fetchall()
    assert rows == []


def test_second_order_injection_ignored(conn, builder):
    payload = "'; DROP TABLE users; --"
    conn.execute("INSERT INTO comments (comment) VALUES (?)", (payload,))
    stored = conn.execute("SELECT comment FROM comments LIMIT 1").fetchone()[0]

    sql, params = builder.build_select("users", ["id"], {"name": stored})
    rows = conn.execute(sql, params).fetchall()
    assert rows == []
    remaining = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    assert remaining == 2


def test_blind_injection_blocked(conn, builder):
    payload = "' OR (SELECT COUNT(*) FROM users)=2 --"
    unsafe_sql = f"SELECT id FROM users WHERE name = '{payload}'"
    unsafe_rows = conn.execute(unsafe_sql).fetchall()
    assert len(unsafe_rows) == 2

    sql, params = builder.build_select("users", ["id"], {"name": payload})
    rows = conn.execute(sql, params).fetchall()
    assert rows == []


def test_union_injection_blocked(conn, builder):
    payload = "' UNION SELECT password FROM users --"
    unsafe_sql = f"SELECT name FROM users WHERE name = '{payload}'"
    unsafe_rows = conn.execute(unsafe_sql).fetchall()
    flat = [r[0] for r in unsafe_rows]
    assert "secret1" in flat or "secret2" in flat

    sql, params = builder.build_select("users", ["name"], {"name": payload})
    rows = conn.execute(sql, params).fetchall()
    assert rows == []


@pytest.mark.performance
def test_query_builder_performance():
    builder = SecureQueryBuilder(
        allowed_tables={"users"}, allowed_columns={"id", "name"}
    )
    n = 1000
    start = time.perf_counter()
    for i in range(n):
        builder.build_select("users", ["id"], {"id": i})
    param_time = time.perf_counter() - start

    start = time.perf_counter()
    for i in range(n):
        f"SELECT id FROM users WHERE id = {i}"
    legacy_time = time.perf_counter() - start

    assert param_time <= legacy_time * 50
