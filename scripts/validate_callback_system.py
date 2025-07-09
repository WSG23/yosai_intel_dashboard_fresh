#!/usr/bin/env python3
"""Validate that callback system and assets are available."""

from pathlib import Path


def validate_callback_system() -> bool:
    try:
        from core.app_factory import create_app

        app = create_app(mode="simple")
        required = ["callback", "unified_callback", "register_callback"]
        missing = [m for m in required if not hasattr(app, m)]
        if missing:
            print(f"\u274c Missing methods: {missing}")
            return False
        print("\u2705 All callback methods available")

        @app.unified_callback(
            outputs="test-output.children",
            inputs="test-input.value",
        )
        def test_cb(value):
            return f"Test: {value}"

        print("\u2705 Callback registration successful")
        return True
    except Exception as e:  # pragma: no cover - best effort
        print(f"\u274c Callback system validation failed: {e}")
        return False


def validate_assets() -> bool:
    required = [
        "assets/navbar_icons/analytics.png",
        "assets/navbar_icons/graphs.png",
        "assets/navbar_icons/export.png",
    ]
    missing = [path for path in required if not Path(path).exists()]
    if missing:
        print(f"\u26a0\ufe0f  Missing assets: {missing}")
        return False
    print("\u2705 All required assets present")
    return True


if __name__ == "__main__":
    print("\U0001f50d Validating callback system and dependencies...")
    ok_callbacks = validate_callback_system()
    ok_assets = validate_assets()
    if ok_callbacks and ok_assets:
        print("\U0001f389 All systems validated successfully!")
    else:
        print("\U0001f4a5 Validation issues found - check logs above")
