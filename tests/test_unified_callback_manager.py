from core.callbacks import UnifiedCallbackManager
from core.error_handling import error_handler


def test_execute_group_with_errors_and_retry():
    manager = UnifiedCallbackManager()

    calls = {"fail": 0}

    def op_success(x):
        return x * 2

    def op_fail(x):
        calls["fail"] += 1
        if calls["fail"] < 2:
            raise ValueError("boom")
        return x + 1

    manager.register_operation("grp", op_success, name="s")
    manager.register_operation("grp", op_fail, name="f", retries=2)

    results = manager.execute_group("grp", 3)
    assert results == [6, 4]


def test_timeout_records_error():
    manager = UnifiedCallbackManager()

    def slow():
        import time
        time.sleep(0.05)
        return True

    manager.register_operation("grp", slow, name="slow", timeout=0.01)
    res = manager.execute_group("grp")
    assert res == [None]
    assert any(ctx.message.startswith("Operation slow") for ctx in error_handler.error_history)
