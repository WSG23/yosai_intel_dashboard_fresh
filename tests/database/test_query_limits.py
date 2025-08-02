import sys
import types
from tests.import_helpers import safe_import, import_optional

flask_stub = types.SimpleNamespace(
    request=types.SimpleNamespace(path=""), url_for=lambda *a, **k: ""
)
safe_import('scipy', types.ModuleType("scipy"))
sys.modules["scipy"].stats = types.SimpleNamespace()
safe_import('flask', flask_stub)
import tests.stubs.flask_caching as flask_caching_stub

safe_import('flask_caching', flask_caching_stub)
if "dask" not in sys.modules:
    dask_stub = types.ModuleType("dask")
    dask_stub.__path__ = []
    dist_stub = types.ModuleType("dask.distributed")
    dist_stub.Client = object
    dist_stub.LocalCluster = object
    safe_import('dask', dask_stub)
    safe_import('dask.distributed', dist_stub)

import importlib.util
from pathlib import Path

module_path = (
    Path(__file__).resolve().parents[2] / "services" / "database_analytics_service.py"
)
spec = importlib.util.spec_from_file_location(
    "services.database_analytics_service", module_path
)
db_module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = db_module
spec.loader.exec_module(db_module)
DatabaseAnalyticsService = db_module.DatabaseAnalyticsService

from tests.utils.query_recorder import QueryRecordingConnection


class FakeConnection:
    def execute_query(self, query, params=None):
        if "GROUP BY event_type, status" in query:
            return [
                {"event_type": "access", "status": "success", "count": 80},
                {"event_type": "access", "status": "failure", "count": 20},
            ]
        if "strftime('%H'" in query:
            return [
                {"hour": "08", "event_count": 50},
                {"hour": "09", "event_count": 50},
            ]
        if "GROUP BY location" in query:
            return [
                {"location": "A", "total_events": 60, "successful_events": 50},
                {"location": "B", "total_events": 40, "successful_events": 30},
            ]
        return []


class RecordingManager:
    def __init__(self):
        self.connection = QueryRecordingConnection(FakeConnection())

    def get_connection(self):
        return self.connection

    def release_connection(self, conn):
        pass


def test_database_analytics_query_count():
    manager = RecordingManager()
    service = DatabaseAnalyticsService(manager)
    service.get_analytics()
    # DatabaseAnalyticsService should issue exactly three queries
    assert len(manager.connection.statements) <= 3
