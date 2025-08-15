import pytest

from validation.file_validator import CSVFormulaRule, FileSizeRule, FileValidator
from validation.rules import CompositeValidator
from validation.security_validator import SecurityValidator, XSSRule


def test_composite_validator_custom_rule():
    class DummyRule(XSSRule):
        called = False

        def validate(self, data: str):
            self.called = True
            return super().validate(data)

    rule = DummyRule()
    validator = CompositeValidator([rule])
    result = validator.validate("<script>")
    assert not result.valid
    assert rule.called


def test_security_validator_blocks_xss():
    validator = SecurityValidator()
    with pytest.raises(Exception):
        validator.validate_input("<script>alert(1)</script>")


def test_security_validator_allows_json():
    validator = SecurityValidator()
    result = validator.validate_input('{"key": "val"}')
    assert result["valid"] is True


def test_file_validator_rules(tmp_path):
    fv = FileValidator(max_size_mb=1)
    data = b"a,b\n1,2"
    ok = fv.validate_file_upload("test.csv", data)
    assert ok["valid"]
    big = b"x" * (2 * 1024 * 1024)
    res = fv.validate_file_upload("big.csv", big)
    assert not res["valid"]
    res = fv.validate_file_upload("bad.txt", data)
    assert not res["valid"]
    bad_formula = b"=cmd(),B"
    res = fv.validate_file_upload("test.csv", bad_formula)
    assert not res["valid"]
