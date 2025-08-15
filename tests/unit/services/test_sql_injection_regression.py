from __future__ import annotations

import importlib.util
import pathlib

import pytest

SRC_PATH = pathlib.Path(__file__).resolve().parents[2] / "yosai_intel_dashboard" / "src"
SPEC = importlib.util.spec_from_file_location(
    "optimized_queries", SRC_PATH / "services" / "optimized_queries.py"
)
optimized_queries = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(optimized_queries)
OptimizedQueryService = optimized_queries.OptimizedQueryService


@pytest.mark.parametrize(
    "payload",
    [
        "' OR 1=1--",  # classic injection
        "'; DROP TABLE users;--",  # second-order
        "' AND 1=pg_sleep(1)--",  # blind
        "' UNION SELECT null--",  # union-based
    ],
)
def test_batch_get_users_blocks_injection(monkeypatch, payload):
    captured: dict[str, object] = {}

    def fake_execute(db, sql, params):  # type: ignore[no-untyped-def]
        captured["sql"] = sql
        captured["params"] = params
        return []

    monkeypatch.setattr(optimized_queries, "execute_secure_query", fake_execute)
    svc = OptimizedQueryService(db=object())
    svc.batch_get_users([payload])
    assert payload not in str(captured["sql"])
    assert payload in captured["params"][0]
