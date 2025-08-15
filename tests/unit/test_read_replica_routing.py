from yosai_intel_dashboard.src.database.replicated_connection import (
    ReplicatedDatabaseConnection,
)


class DummyConnection:
    def __init__(self) -> None:
        self.queries = []
        self.commands = []

    def execute_query(self, query, params=None):  # pragma: no cover - simple
        self.queries.append(query)
        return []

    def execute_command(self, command, params=None):  # pragma: no cover - simple
        self.commands.append(command)

    def prepare_statement(self, name, query):  # pragma: no cover - simple
        pass

    def execute_prepared(self, name, params):  # pragma: no cover - simple
        self.queries.append(name)
        return []

    def health_check(self):  # pragma: no cover - simple
        return True


def test_read_queries_use_replica():
    primary = DummyConnection()
    replica = DummyConnection()
    conn = ReplicatedDatabaseConnection(primary, [replica])

    conn.execute_query("SELECT 1")
    conn.execute_command("UPDATE t SET x=1")

    assert primary.commands == ["UPDATE t SET x=1"]
    assert replica.queries == ["SELECT 1"]
    assert not primary.queries
    assert not replica.commands
