from __future__ import annotations

import sys
import types


def test_custom_retry_strategy_used():
    module_name = "yosai_intel_dashboard.src.infrastructure.config.database_manager"
    stub_module = types.ModuleType(module_name)

    class MockConnection:
        def health_check(self) -> bool:  # pragma: no cover - simple stub
            return True

        def close(self) -> None:  # pragma: no cover - simple stub
            pass

    class StubManager:
        def __init__(self, config) -> None:  # pragma: no cover - simple stub
            pass

        def get_connection(self):  # pragma: no cover - simple stub
            return MockConnection()

    stub_module.DatabaseManager = StubManager
    stub_module.MockConnection = MockConnection
    sys.modules[module_name] = stub_module

    db_conn_module_name = "yosai_intel_dashboard.src.database.connection"
    db_conn_module = types.ModuleType(db_conn_module_name)
    sys.modules[db_conn_module_name] = db_conn_module
    sys.modules["database.connection"] = db_conn_module

    query_opt_name = "yosai_intel_dashboard.src.services.query_optimizer"
    sys.modules[query_opt_name] = types.ModuleType(query_opt_name)

    from yosai_intel_dashboard.src.infrastructure.config import (
        database_connection_factory as dcf,
    )

    class StubStrategy:
        def __init__(self) -> None:
            self.calls = 0

        def run_with_retry(self, func):  # type: ignore[override]
            self.calls += 1
            return func()

    cfg = object()
    strategy = StubStrategy()
    factory = dcf.DatabaseConnectionFactory(cfg, retry_strategy=strategy)
    conn = factory.create()
    assert isinstance(conn, MockConnection)
    assert strategy.calls == 1
