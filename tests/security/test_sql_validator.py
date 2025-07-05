import pytest

from security.sql_validator import SQLInjectionPrevention
from core.exceptions import ValidationError


def test_injection_vectors(caplog):
    validator = SQLInjectionPrevention()
    payloads = [
        "' OR 1=1 --",
        "1; DROP TABLE users",
        "UNION SELECT password FROM users",
        "/*comment*/SELECT * FROM data",
    ]
    for payload in payloads:
        with caplog.at_level("WARNING"):
            with pytest.raises(ValidationError):
                validator.validate_query_parameter(payload)
            assert any("Security alert" in r.getMessage() for r in caplog.records)
            caplog.clear()


def test_encoded_payload():
    validator = SQLInjectionPrevention()
    with pytest.raises(ValidationError):
        validator.validate_query_parameter("%53%45%4C%45%43%54")


def test_legitimate_inputs():
    validator = SQLInjectionPrevention()
    assert validator.validate_query_parameter("john_doe") == "john_doe"
    assert validator.validate_query_parameter(123) == "123"


def test_performance_large_batch():
    validator = SQLInjectionPrevention()
    for _ in range(10000):
        validator.validate_query_parameter("safe")


def test_validate_sql_statement():
    validator = SQLInjectionPrevention()
    with pytest.raises(ValidationError):
        validator.validate_sql_statement("DROP TABLE foo")
    with pytest.raises(ValidationError):
        validator.validate_sql_statement("SELECT 1; SELECT 2")
    assert validator.validate_sql_statement("SELECT * FROM foo WHERE id = ?")


def test_enforce_parameterization():
    validator = SQLInjectionPrevention()
    with pytest.raises(ValidationError):
        validator.enforce_parameterization("SELECT * FROM t WHERE id=?", None)
    with pytest.raises(ValidationError):
        validator.enforce_parameterization("SELECT * FROM t", ("a",))
    validator.enforce_parameterization(
        "SELECT * FROM t WHERE id=? AND name=?", ("1", "a")
    )
