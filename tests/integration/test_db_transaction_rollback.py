from __future__ import annotations

from typing import Any, Optional, Protocol

import pandas as pd
import pytest


class DatabaseProtocol(Protocol):
    def execute_query(
        self, query: str, params: Optional[tuple] = None
    ) -> pd.DataFrame: ...

    def execute_command(self, command: str, params: Optional[tuple] = None) -> None: ...

    def begin_transaction(self) -> Any: ...

    def commit_transaction(self, transaction: Any) -> None: ...

    def rollback_transaction(self, transaction: Any) -> None: ...

    def health_check(self) -> bool: ...

    def get_connection_info(self) -> dict: ...


class MockDatabase(DatabaseProtocol):
    def __init__(self) -> None:
        self.data: list[str] = ["initial"]

    def execute_query(self, query: str, params: tuple | None = None) -> pd.DataFrame:
        return pd.DataFrame({"value": self.data})

    def execute_command(self, command: str, params: tuple | None = None) -> None:
        self.data.append(command)

    def prepare_statement(
        self, name: str, query: str
    ) -> None:  # pragma: no cover - protocol compliance
        pass

    def execute_prepared(
        self, name: str, params: tuple
    ) -> pd.DataFrame:  # pragma: no cover - protocol compliance
        return pd.DataFrame({"value": self.data})

    def begin_transaction(self) -> dict:
        return {"snapshot": list(self.data)}

    def commit_transaction(self, transaction: dict) -> None:
        pass

    def rollback_transaction(self, transaction: dict) -> None:
        self.data = transaction["snapshot"]

    def health_check(self) -> bool:
        return True

    def get_connection_info(self) -> dict:
        return {}


@pytest.fixture
def mock_db() -> DatabaseProtocol:
    return MockDatabase()


def test_db_transaction_rollback(mock_db: DatabaseProtocol) -> None:
    pre_state = mock_db.execute_query("SELECT")
    transaction = mock_db.begin_transaction()

    with pytest.raises(RuntimeError):
        try:
            mock_db.execute_command("INSERT new")
            raise RuntimeError("boom")
            mock_db.commit_transaction(transaction)
        except RuntimeError:
            mock_db.rollback_transaction(transaction)
            raise

    post_state = mock_db.execute_query("SELECT")
    pd.testing.assert_frame_equal(post_state, pre_state)
