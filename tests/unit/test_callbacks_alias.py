import yosai_intel_dashboard.src.infrastructure.callbacks as callbacks


def test_unified_callback_manager_removed():
    assert not hasattr(callbacks, "UnifiedCallbackManager")
