import html

import pytest

from validation.security_validator import SecurityValidator


def test_sql_injection_validation():
    validator = SecurityValidator()
    with pytest.raises(Exception):
        validator.validate_input("1; DROP TABLE users")


def test_main_validation_orchestration():
    validator = SecurityValidator()
    value = "<script>alert('xss')</script>"
    with pytest.raises(Exception):
        validator.validate_input(value, "comment")


def test_validate_file_upload_rules():
    validator = SecurityValidator()
    valid = validator.validate_file_upload("ok.csv", b"a,b\n1,2")
    assert valid["valid"]
    with pytest.raises(Exception):
        validator.validate_file_upload("bad.csv", b"=cmd()")
