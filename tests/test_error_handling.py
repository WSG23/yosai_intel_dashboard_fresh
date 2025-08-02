import logging

import pytest

from yosai_intel_dashboard.src.core.error_handling import (
    ErrorCategory,
    ErrorHandler,
    ErrorSeverity,
    with_error_handling,
)


def test_handle_error_returns_context(caplog):
    handler = ErrorHandler(logger=logging.getLogger("test"))
    with caplog.at_level(logging.WARNING):
        ctx = handler.handle_error(
            ValueError("boom"),
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.HIGH,
            context={"a": 1},
        )
    assert ctx.message == "boom"
    assert ctx.category is ErrorCategory.DATABASE
    assert ctx.severity is ErrorSeverity.HIGH
    assert ctx.details == {"a": 1}
    assert ctx in handler.error_history
    assert any("boom" in r.getMessage() for r in caplog.records)


def test_with_error_handling_decorator(monkeypatch, caplog):
    handler = ErrorHandler(logger=logging.getLogger("test"))
    monkeypatch.setattr("core.error_handling.error_handler", handler)

    @with_error_handling(
        category=ErrorCategory.CONFIGURATION, severity=ErrorSeverity.MEDIUM
    )
    def fail():
        raise RuntimeError("oops")

    with caplog.at_level(logging.WARNING):
        result = fail()
    assert result is None
    assert handler.error_history
    assert handler.error_history[-1].message == "oops"
    assert any("oops" in r.getMessage() for r in caplog.records)

    @with_error_handling(reraise=True)
    def fail_raise():
        raise RuntimeError("again")

    with pytest.raises(RuntimeError):
        fail_raise()
    assert handler.error_history[-1].message == "again"
