"""Callback debugging helpers."""

from yosai_intel_dashboard.src.core.app_factory import create_app
from yosai_intel_dashboard.src.core.callback_registry import _callback_registry


def debug_callback_conflicts() -> None:
    """Print callback registration info and detect conflicts."""
    create_app()
    print("\U0001f50d Callback Registration Analysis:")
    print(f"Total registered callbacks: {len(_callback_registry.registered_callbacks)}")
    for cid, source in _callback_registry.callback_sources.items():
        print(f"  \u2705 {cid} (from {source})")
    conflicts = _callback_registry.get_conflicts()
    if conflicts:
        print("\u26a0\ufe0f Potential conflicts found")
    else:
        print("\u2705 No callback conflicts detected")


def validate_callback_system() -> bool:
    """Verify callback methods are available and registration works."""
    try:
        app = create_app(mode="simple")
        required = ["callback", "unified_callback", "register_callback"]
        missing = [m for m in required if not hasattr(app, m)]
        if missing:
            print(f"\u274c Missing methods: {missing}")
            return False
        print("\u2705 All callback methods available")

        @app.unified_callback(outputs="test-output.children", inputs="test-input.value")
        def test_cb(value):
            return f"Test: {value}"  # pragma: no cover - sanity example

        print("\u2705 Callback registration successful")
        return True
    except Exception as e:  # pragma: no cover - best effort
        print(f"\u274c Callback system validation failed: {e}")
        return False


__all__ = ["debug_callback_conflicts", "validate_callback_system"]
