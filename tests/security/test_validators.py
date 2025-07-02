import pandas as pd
import pytest

from core.input_validation import InputValidator
from security.dataframe_validator import DataFrameSecurityValidator
from security.sql_validator import SQLInjectionPrevention
from security.xss_validator import XSSPrevention
from security.validation_exceptions import ValidationError


def test_unicode_normalization():
    validator = InputValidator()
    with pytest.raises(ValidationError):
        validator.validate("<bad>")


def test_html_js_injection_attempts():
    validator = InputValidator()
    payloads = [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert(1)>",
    ]
    for payload in payloads:
        with pytest.raises(ValidationError):
            validator.validate(payload)


def test_json_input_allowed():
    validator = InputValidator()
    # Should not raise ValidationError for quotes within JSON structures
    validator.validate('{"key":"val"}')


def test_sql_injection_detection():
    with pytest.raises(ValidationError):
        SQLInjectionPrevention.validate_query_parameter("1; DROP TABLE users")


def test_xss_sanitization():
    result = XSSPrevention.sanitize_html_output("<script>alert('xss')</script>")
    assert "<" not in result and ">" not in result


def test_dataframe_memory_limit(monkeypatch):
    df = pd.DataFrame({"a": range(100)})
    validator = DataFrameSecurityValidator()
    monkeypatch.setattr("config.dynamic_config.security.max_upload_mb", 0)
    with pytest.raises(ValidationError):
        validator.validate_for_upload(df)


def test_csv_injection_detection():
    df = pd.DataFrame({"a": ["=cmd()"]})
    validator = DataFrameSecurityValidator()
    with pytest.raises(ValidationError):
        validator.validate_for_upload(df)


def test_csv_safe_dataframe_allowed():
    df = pd.DataFrame({"a": ["cmd()", "ok"]})
    validator = DataFrameSecurityValidator()
    result = validator.validate_for_upload(df)
    assert isinstance(result, pd.DataFrame)


def _create_test_app():
    from flask import Flask
    from security.validation_middleware import ValidationMiddleware

    app = Flask(__name__)
    middleware = ValidationMiddleware()
    app.before_request(middleware.validate_request)
    app.after_request(middleware.sanitize_response)

    @app.route("/", methods=["GET", "POST"])
    def index():
        return "ok"

    return app


def test_oversized_upload_rejected(monkeypatch):
    monkeypatch.setattr("config.dynamic_config.security.max_upload_mb", 0)
    app = _create_test_app()
    client = app.test_client()
    resp = client.post("/", data="A" * 1024)
    assert resp.status_code == 413


def test_malicious_query_rejected():
    app = _create_test_app()
    client = app.test_client()
    resp = client.get("/?q=%3Cscript%3E")
    assert resp.status_code == 400
