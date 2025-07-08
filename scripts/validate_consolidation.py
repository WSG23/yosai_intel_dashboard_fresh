#!/usr/bin/env python3
"""Validate Phase 3-4 consolidation is complete."""
import sys
from pathlib import Path

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


def check_file_structure():
    """Check that duplicate files are removed."""
    root = Path(__file__).parent.parent

    duplicates = [
        "components/upload/drag_drop_upload_area.py",
        "components/advanced_upload.py",
        "components/file_upload_component.py",
    ]

    existing = []
    for dup in duplicates:
        if (root / dup).exists():
            existing.append(dup)

    if existing:
        print(f"❌ Duplicate files still exist: {existing}")
        return False

    print("✅ File structure consolidation complete")
    return True


def check_di_integration():
    """Check DI integration is working."""
    try:
        from core.app_factory import create_app
        from core.service_container import ServiceContainer

        app = create_app({"TESTING": True})
        assert app is not None

        factory = app._yosai_app_factory
        container = factory.get_container()
        assert isinstance(container, ServiceContainer)

        # Test key services are registered
        services = [
            "upload_processor",
            "upload_validator",
            "file_processor",
            "config_manager",
        ]

        for service in services:
            assert container.has(service), f"Service {service} not registered"

        print("✅ DI integration working correctly")
        return True

    except Exception as e:
        print(f"❌ DI integration failed: {e}")
        return False


if __name__ == "__main__":
    file_ok = check_file_structure()
    di_ok = check_di_integration()

    if file_ok and di_ok:
        print("\n🎉 Phase 3-4 consolidation COMPLETE!")
        sys.exit(0)
    else:
        print("\n❌ Consolidation issues found")
        sys.exit(1)
