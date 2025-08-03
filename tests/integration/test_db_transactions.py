from __future__ import annotations

import pandas as pd
import pytest

from yosai_intel_dashboard.src.core.protocols import DatabaseProtocol


class InMemoryDatabase(DatabaseProtocol):
    def __init__(self) -> None:
        self.data: list[str] = []
        self.rollback_called = False

    def execute_query(self, query: str, params: tuple | None = None) -> pd.DataFrame:
        return pd.DataFrame(self.data)

    def execute_command(self, command: str, params: tuple | None = None) -> None:
        self.data.append(command)

    def begin_transaction(self) -> dict:
        return {"snapshot": list(self.data)}

    def commit_transaction(self, transaction: dict) -> None:
        pass

    def rollback_transaction(self, transaction: dict) -> None:
        self.rollback_called = True
        self.data = transaction["snapshot"]

    def health_check(self) -> bool:
        return True

    def get_connection_info(self) -> dict:
        return {}


@pytest.fixture
def db() -> DatabaseProtocol:
    return InMemoryDatabase()


def test_rollback_on_error(db: DatabaseProtocol) -> None:
    transaction = db.begin_transaction()
    with pytest.raises(RuntimeError):
        try:
            db.execute_command("INSERT 1")
            raise RuntimeError("fail")
            db.commit_transaction(transaction)
        except RuntimeError:
            db.rollback_transaction(transaction)
            raise

    assert db.rollback_called
    assert db.data == []
