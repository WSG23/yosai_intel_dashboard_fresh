class TestSecurityVulnerabilities:
    """Comprehensive security vulnerability tests."""

    def test_sql_injection_prevention(self):
        """Test SQL injection attack patterns."""
        import pytest
        from security.sql_validator import SQLInjectionPrevention
        from security.validation_exceptions import ValidationError

        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'/**/OR/**/1=1#",
        ]
        validator = SQLInjectionPrevention()

        for malicious_input in malicious_inputs:
            with pytest.raises(ValidationError):
                validator.validate_query_parameter(malicious_input)

    def test_unicode_surrogate_handling(self):
        """Test Unicode surrogate character handling."""
        from utils.unicode_handler import sanitize_unicode_input

        # Test lone surrogates
        lone_surrogate = "\uD800\uD801"  # Invalid surrogate pair
        result = sanitize_unicode_input(lone_surrogate)
        assert "\uD800" not in result
        assert "\uD801" not in result
        assert "\ufffd" in result

    def test_sanitize_unicode_input_ascii_fallback(self):
        """Ensure ASCII-safe text is returned on failure."""
        from utils.unicode_handler import sanitize_unicode_input

        class BadStr:
            def __str__(self) -> str:
                raise UnicodeError("boom")

        result = sanitize_unicode_input(BadStr())
        assert result.isascii()
