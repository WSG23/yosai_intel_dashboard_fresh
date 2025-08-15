import sqlite3
from datetime import datetime
from typing import Iterable
from importlib import util
from pathlib import Path

spec = util.spec_from_file_location(
    "optimized_queries",
    str(Path(__file__).resolve().parents[2] / "services" / "optimized_queries.py"),
)
optimized_queries = util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(optimized_queries)
OptimizedQueryService = optimized_queries.OptimizedQueryService


class _Conn:
    def __init__(self) -> None:
        self.conn = sqlite3.connect(":memory:", check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

    def execute_query(self, query: str, params: tuple | None = None):
        cur = self.conn.cursor()
        cur.execute(query.replace("%s", "?"), params or ())
        rows = cur.fetchall()
        return [dict(r) for r in rows]

    def execute_command(self, command: str, params: tuple | None = None):
        cur = self.conn.cursor()
        cur.execute(command.replace("%s", "?"), params or ())
        self.conn.commit()
        return cur.rowcount

    def execute_batch(self, command: str, params_seq: Iterable[tuple]):
        cur = self.conn.cursor()
        cur.executemany(command.replace("%s", "?"), params_seq)
        self.conn.commit()

    def health_check(self) -> bool:
        try:
            self.conn.execute("SELECT 1")
            return True
        except Exception:
            return False


def setup_db():
    c = _Conn()
    c.execute_command(
        """CREATE TABLE people (
               person_id TEXT PRIMARY KEY,
               name TEXT
           )"""
    )
    c.execute_command(
        """CREATE TABLE doors (
               door_id TEXT PRIMARY KEY,
               facility_id TEXT
           )"""
    )
    c.execute_command(
        """CREATE TABLE access_events (
               event_id TEXT PRIMARY KEY,
               timestamp TEXT,
               person_id TEXT,
               door_id TEXT
           )"""
    )
    c.execute_command(
        "INSERT INTO people (person_id, name) VALUES ('U1', 'Alice'), ('U2', 'Bob')"
    )
    c.execute_command("INSERT INTO doors (door_id, facility_id) VALUES ('D1', 'F1')")
    ts = datetime.now().isoformat()
    c.execute_command(
        "INSERT INTO access_events (event_id, timestamp, person_id, door_id) VALUES ('E1', ?, 'U1', 'D1')",
        (ts,),
    )
    return c


def test_get_events_with_users():
    db = setup_db()
    svc = OptimizedQueryService(db)
    rows = svc.get_events_with_users("F1")
    assert rows
    assert rows[0]["event_id"] == "E1"
    assert rows[0]["name"] == "Alice"


def test_batch_get_users():
    db = setup_db()
    svc = OptimizedQueryService(db)
    users = svc.batch_get_users(["U1", "U2"])
    assert {u["person_id"] for u in users} == {"U1", "U2"}
