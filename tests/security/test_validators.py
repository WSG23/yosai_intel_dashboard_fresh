import pandas as pd
import pytest
from types import SimpleNamespace

from tests.import_helpers import safe_import

stub_dynamic_config = SimpleNamespace(
    security=SimpleNamespace(max_upload_mb=1),
    upload=SimpleNamespace(allowed_file_types=[".csv", ".json", ".xlsx", ".xls"]),
)
safe_import("config", SimpleNamespace())
safe_import("config.dynamic_config", SimpleNamespace(dynamic_config=stub_dynamic_config))

from validation.security_validator import SecurityValidator


def test_unicode_normalization():
    validator = SecurityValidator()
    res = validator.validate_input("<script>")
    assert res.valid is False


def test_html_js_injection_attempts():
    validator = SecurityValidator()
    payloads = [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert(1)>",
    ]
    for payload in payloads:
        res = validator.validate_input(payload)
        assert res.valid is False


def test_json_input_allowed():
    validator = SecurityValidator()
    res = validator.validate_input('{"key":"val"}')
    assert res.valid


def test_sql_injection_detection():
    validator = SecurityValidator()
    res = validator.validate_input("1; DROP TABLE users", "query_parameter")
    assert res.valid is False
    assert "sql_injection" in (res.issues or [])


def test_file_size_limit(monkeypatch):
    df = pd.DataFrame({"a": range(100)})
    monkeypatch.setattr("config.dynamic_config.security.max_upload_mb", 0)
    validator = SecurityValidator()
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    res = validator.validate_file_upload("data.csv", csv_bytes)
    assert res.valid is False


def test_csv_injection_detection():
    df = pd.DataFrame({"a": ["=cmd()"]})
    validator = SecurityValidator()
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    res = validator.validate_file_upload("data.csv", csv_bytes)
    assert res.valid is False


def test_csv_safe_dataframe_allowed():
    df = pd.DataFrame({"a": ["cmd()", "ok"]})
    validator = SecurityValidator()
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    result = validator.validate_file_upload("data.csv", csv_bytes)
    assert result.valid is True


def test_oversized_upload_rejected(monkeypatch):
    monkeypatch.setattr("config.dynamic_config.security.max_upload_mb", 0)
    validator = SecurityValidator()
    res = validator.validate_file_upload("data.csv", b"A" * 1024)
    assert res.valid is False


def test_malicious_query_rejected():
    validator = SecurityValidator()
    res = validator.scan_query("SELECT * FROM users; DROP TABLE users;")
    assert res.valid is False


def test_validate_resource_id():
    validator = SecurityValidator()
    good = validator.validate_resource_id("res_123-abc")
    bad = validator.validate_resource_id("../etc/passwd")
    assert good.valid is True
    assert bad.valid is False

