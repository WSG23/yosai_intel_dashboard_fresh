#!/usr/bin/env python3
"""Test that critical modules can be imported without dependency errors."""


def test_imports() -> bool:
    modules_to_test = [
        "core.security_validator",
        "services.analytics.upload_analytics",
        "services.chunked_analysis",
        "config",
        "utils",
        "security_callback_controller",
    ]

    success = True
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"\u2705 {module}")
        except Exception as exc:  # pragma: no cover - simple diagnostic
            print(f"\u274c {module}: {exc}")
            success = False
    return success


if __name__ == "__main__":
    if test_imports():
        print("\U0001F389 All imports working!")
    else:
        print("\U0001F4A5 Import issues remain")
