from __future__ import annotations

import importlib
import sys
import types

from yosai_intel_dashboard.src.database.mock_database import MockDatabase


def test_baseline_metrics_uses_parameters(monkeypatch):
    mock_db = MockDatabase()
    fake_conn = types.SimpleNamespace(create_database_connection=lambda: mock_db)
    fake_sec = types.SimpleNamespace(
        execute_secure_command=lambda c, s, p=None: c.execute_command(s, p),
        execute_secure_sql=lambda c, s, p=None: c.execute_query(s, p),
    )
    fake_secure_query = types.SimpleNamespace(
        SecureQueryBuilder=lambda **_: types.SimpleNamespace(
            table=lambda x: x, build=lambda sql, params=None, logger=None: (sql, params)
        )
    )
    monkeypatch.setitem(sys.modules, "database.connection", fake_conn)
    monkeypatch.setitem(sys.modules, "security", types.ModuleType("security"))
    monkeypatch.setitem(sys.modules, "security.secure_query_wrapper", fake_sec)
    monkeypatch.setitem(
        sys.modules, "yosai_intel_dashboard.src.infrastructure.security.query_builder", fake_secure_query
    )
    bm = importlib.import_module("yosai_intel_dashboard.src.database.baseline_metrics")
    importlib.reload(bm)
    db = bm.BaselineMetricsDB()
    malicious = "1'; DROP TABLE users; --"
    db.update_baseline("user", malicious, {"views": 1.0})
    command, params = mock_db.commands[-1]
    assert malicious not in command
    assert params == ("user", malicious, "views", 1.0)

    db.get_baseline("user", malicious)
    query, qparams = mock_db.queries[-1]
    assert malicious not in query
    assert qparams == ("user", malicious)
