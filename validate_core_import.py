#!/usr/bin/env python3
"""Test that core module imports without errors"""

def test_core_import():
    try:
        import core
        print("\N{white heavy check mark} core module imports successfully")
        return True
    except NameError as e:
        print(f"\N{cross mark} NameError: {e}")
        return False
    except ImportError as e:
        print(f"\N{cross mark} ImportError: {e}")
        return False

if __name__ == "__main__":
    success = test_core_import()
    if success:
        print("\U0001F389 Type import issue resolved!")
    else:
        print("\U0001F4A5 Still has import issues")
