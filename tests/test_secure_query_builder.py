import logging

import pytest

import importlib.util
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "secure_query",
    Path(__file__).resolve().parents[1]
    / "yosai_intel_dashboard/src/infrastructure/database/secure_query.py",
)
secure_query = importlib.util.module_from_spec(spec)
sys.modules["secure_query"] = secure_query
spec.loader.exec_module(secure_query)  # type: ignore
SecureQueryBuilder = secure_query.SecureQueryBuilder


def test_rejects_malicious_table_name():
    builder = SecureQueryBuilder(allowed_tables={"access_events"})
    with pytest.raises(ValueError):
        builder.table("access_events; DROP TABLE users;")


def test_rejects_malicious_column_name():
    builder = SecureQueryBuilder(allowed_columns={"id"})
    with pytest.raises(ValueError):
        builder.column("id; DROP TABLE users;")


def test_log_redaction(caplog):
    builder = SecureQueryBuilder(allowed_tables={"access_events"})
    table = builder.table("access_events")
    logger = logging.getLogger("secure_test")
    with caplog.at_level(logging.DEBUG, logger="secure_test"):
        builder.build(
            f"SELECT * FROM {table} WHERE id=%s",
            (123,),
            logger=logger,
        )
    assert "123" not in caplog.text
    assert "?" in caplog.text
