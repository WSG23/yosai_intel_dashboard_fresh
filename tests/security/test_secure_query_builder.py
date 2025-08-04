import importlib.util
import pathlib
import sys

import pytest

SRC_PATH = pathlib.Path(__file__).resolve().parents[2] / "yosai_intel_dashboard" / "src"
SECURE_QUERY_FILE = SRC_PATH / "infrastructure" / "database" / "secure_query.py"
spec = importlib.util.spec_from_file_location(
    "infrastructure.database.secure_query", SECURE_QUERY_FILE
)
secure_query = importlib.util.module_from_spec(spec)
sys.modules["infrastructure.database.secure_query"] = secure_query
spec.loader.exec_module(secure_query)
SecureQueryBuilder = secure_query.SecureQueryBuilder


def test_secure_query_builder_blocks_table_injection():
    builder = SecureQueryBuilder(allowed_tables={"consent_log"})
    with pytest.raises(ValueError):
        builder.table("consent_log; DROP TABLE users;--")
