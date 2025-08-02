class TestSecurityVulnerabilities:
    """Comprehensive security vulnerability tests."""

    def test_sql_injection_prevention(self):
        """Test SQL injection attack patterns."""
        import pytest

        from yosai_intel_dashboard.src.core.exceptions import ValidationError
        from validation.security_validator import SecurityValidator

        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'/**/OR/**/1=1#",
        ]
        validator = SecurityValidator()

        for malicious_input in malicious_inputs:
            with pytest.raises(ValidationError):
                validator.validate_input(malicious_input, "query_parameter")

    def test_unicode_surrogate_handling(self):
        """Test Unicode surrogate character handling."""
        from yosai_intel_dashboard.src.core.unicode import sanitize_unicode_input

        # Test lone surrogates
        lone_surrogate = "\ud800\ud801"  # Invalid surrogate pair
        result = sanitize_unicode_input(lone_surrogate)
        assert "\ud800" not in result
        assert "\ud801" not in result
        assert "\ufffd" in result

    def test_sanitize_unicode_input_ascii_fallback(self):
        """Ensure ASCII-safe text is returned on failure."""
        from yosai_intel_dashboard.src.core.unicode import sanitize_unicode_input

        class BadStr:
            def __str__(self) -> str:
                raise UnicodeError("boom")

        result = sanitize_unicode_input(BadStr())
        assert result.isascii()
