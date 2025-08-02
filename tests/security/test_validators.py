import pandas as pd
import pytest

from yosai_intel_dashboard.src.core.exceptions import ValidationError
from security.xss_validator import XSSPrevention
from validation.security_validator import SecurityValidator


def test_unicode_normalization():
    validator = SecurityValidator()
    with pytest.raises(ValidationError):
        validator.validate_input("<script>")


def test_html_js_injection_attempts():
    validator = SecurityValidator()
    payloads = [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert(1)>",
    ]
    for payload in payloads:
        with pytest.raises(ValidationError):
            validator.validate_input(payload)


def test_json_input_allowed():
    validator = SecurityValidator()
    # Should not raise ValidationError for quotes within JSON structures
    validator.validate_input('{"key":"val"}')


def test_sql_injection_detection():
    validator = SecurityValidator()
    with pytest.raises(ValidationError):
        validator.validate_input("1; DROP TABLE users", "query_parameter")


def test_xss_sanitization():
    result = XSSPrevention.sanitize_html_output("<script>alert('xss')</script>")
    assert "<" not in result and ">" not in result


def test_file_size_limit(monkeypatch):
    df = pd.DataFrame({"a": range(100)})
    monkeypatch.setattr("config.dynamic_config.security.max_upload_mb", 0)
    validator = SecurityValidator()
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    with pytest.raises(ValidationError):
        validator.validate_file_upload("data.csv", csv_bytes)


def test_csv_injection_detection():
    df = pd.DataFrame({"a": ["=cmd()"]})
    validator = SecurityValidator()
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    with pytest.raises(ValidationError):
        validator.validate_file_upload("data.csv", csv_bytes)


def test_csv_safe_dataframe_allowed():
    df = pd.DataFrame({"a": ["cmd()", "ok"]})
    validator = SecurityValidator()
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    result = validator.validate_file_upload("data.csv", csv_bytes)
    assert result["valid"] is True


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
