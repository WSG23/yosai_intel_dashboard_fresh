#!/usr/bin/env python3
"""Debug callback registration conflicts and validate fixes"""

from core.app_factory import create_app
from core.callback_registry import _callback_registry


def debug_callback_conflicts():
    app = create_app()
    print("\ud83d\udd0d Callback Registration Analysis:")
    print(f"Total registered callbacks: {len(_callback_registry.registered_callbacks)}")
    for cid, source in _callback_registry.registration_sources.items():
        print(f"  \u2705 {cid} (from {source})")
    conflicts = _callback_registry.get_conflicts()
    if conflicts:
        print("\u26a0\ufe0f Potential conflicts found")
    else:
        print("\u2705 No callback conflicts detected")


def validate_assets():
    from pathlib import Path

    required_icons = [
        "assets/navbar_icons/analytics.png",
        "assets/navbar_icons/graphs.png",
        "assets/navbar_icons/export.png",
        "assets/navbar_icons/settings.png",
        "assets/navbar_icons/upload.png",
    ]
    missing = [icon for icon in required_icons if not Path(icon).exists()]
    if missing:
        print(f"\u274c Missing assets: {missing}")
        return False
    print("\u2705 All navbar assets present")
    return True


if __name__ == "__main__":
    debug_callback_conflicts()
    validate_assets()
