from __future__ import annotations

import pytest

from validation.security_validator import SecurityValidator
from yosai_intel_dashboard.src.core.exceptions import ValidationError


@pytest.mark.parametrize(
    "input_type,payload",
    [
        ("sql", "1; DROP TABLE users"),
        ("nosql", '{"$where":"this.password==\'a\'"}'),
        ("ldap", "*)(uid=*))(|(uid=*"),
        ("xpath", "' or 1=1 or 'x'='x"),
        ("command", "whoami && rm -rf /"),
    ],
)
def test_injection_patterns_raise(input_type, payload):
    validator = SecurityValidator()
    with pytest.raises(ValidationError):
        validator.validate_input(payload, input_type=input_type)


def test_html_is_escaped():
    validator = SecurityValidator()
    result = validator.validate_input("<b>bold</b>", input_type="html")
    assert result["sanitized"] == "&lt;b&gt;bold&lt;/b&gt;"


def test_json_validates_and_canonicalizes():
    validator = SecurityValidator()
    result = validator.validate_input('{"a":1}', input_type="json")
    assert result["sanitized"] == '{"a": 1}'


def test_json_invalid_raises():
    validator = SecurityValidator()
    with pytest.raises(ValidationError):
        validator.validate_input('{"a":1,}', input_type="json")
