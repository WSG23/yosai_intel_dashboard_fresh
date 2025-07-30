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
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, safe_str(PROJECT_ROOT))

try:
    logger.info("🔍 Testing base code imports...")

    from config.service_registration import register_upload_services

    logger.info("✅ Service registration imported")

    from core.service_container import ServiceContainer

    logger.info("✅ Service container imported")

    container = ServiceContainer()
    logger.info("✅ Container created")

    register_upload_services(container)
    logger.info("✅ Services registered")

    upload_service = container.get("upload_processor")
    logger.info("✅ Upload service: %s", type(upload_service))

    logger.info("🎉 All base code services loaded successfully!")

except Exception as e:
    logger.exception("❌ Base code error: %s", e)
