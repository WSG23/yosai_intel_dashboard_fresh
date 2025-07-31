#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test base code service loading"""


def safe_str(obj):
    """Handle unicode and encoding issues."""
    try:
        if isinstance(obj, bytes):
            return obj.decode("utf-8", errors="replace")
        return (
            str(obj).encode("utf-8", errors="ignore").decode("utf-8", errors="replace")
        )
    except:
        return repr(obj)


import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, safe_str(PROJECT_ROOT))

try:
    print("🔍 Testing base code imports...")

    from services.upload.service_registration import register_upload_services

    print("✅ Service registration imported")

    from core.service_container import ServiceContainer

    print("✅ Service container imported")

    container = ServiceContainer()
    print("✅ Container created")

    register_upload_services(container)
    print("✅ Services registered")

    upload_service = container.get("upload_processor")
    print(f"✅ Upload service: {type(upload_service)}")

    print("🎉 All base code services loaded successfully!")

except Exception as e:
    print(f"❌ Base code error: {e}")
    import traceback

    traceback.print_exc()
