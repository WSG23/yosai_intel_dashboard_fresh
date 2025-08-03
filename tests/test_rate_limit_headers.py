from __future__ import annotations

import sys
import time
import types

# Stub out heavy SecurityValidator dependency before import
validator_stub = types.ModuleType("validation.security_validator")
validator_stub.SecurityValidator = object  # type: ignore[attr-defined]
sys.modules["validation.security_validator"] = validator_stub

from yosai_intel_dashboard.src.core.security import RateLimiter


def test_rate_limiter_returns_header_fields():
    limiter = RateLimiter(max_requests=2, window_minutes=1)
    result1 = limiter.is_allowed("user")
    assert result1["allowed"] is True
    assert result1["limit"] == 2
    assert result1["remaining"] == 1
    assert result1["reset"] > time.time()

    result2 = limiter.is_allowed("user")
    assert result2["allowed"] is True
    assert result2["remaining"] == 0

    result3 = limiter.is_allowed("user")
    assert result3["allowed"] is False
    assert result3["retry_after"] > 0
    assert result3["remaining"] == 0
    assert result3["limit"] == 2
