from yosai_intel_dashboard.src.database.mock_database import MockDatabase
from yosai_intel_dashboard.src.database.protocols import ConnectionProtocol


def test_mock_database_conforms_to_protocol() -> None:
    db = MockDatabase()
    assert isinstance(db, ConnectionProtocol)

    assert db.execute_query("SELECT 1") == []
    assert db.fetch_results("SELECT 1") == []
    assert db.execute_command("UPDATE t SET a=1") == 0
    assert db.health_check() is True
    db.close()
    assert db.health_check() is False
