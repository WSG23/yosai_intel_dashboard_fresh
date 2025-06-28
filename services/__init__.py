#!/usr/bin/env python3
"""
Simplified Services Package
"""
import logging

logger = logging.getLogger(__name__)

# Only import existing services
try:
    from .file_processor import FileProcessor
    FILE_PROCESSOR_AVAILABLE = True
except ImportError:
    logger.warning("File processor not available")
    FILE_PROCESSOR_AVAILABLE = False
    FileProcessor = None

try:
    from .analytics_service import get_analytics_service, create_analytics_service, AnalyticsService
    ANALYTICS_SERVICE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Analytics service not available: {e}")
    get_analytics_service = None
    create_analytics_service = None
    AnalyticsService = None
    ANALYTICS_SERVICE_AVAILABLE = False

__all__ = [
    'FileProcessor', 'FILE_PROCESSOR_AVAILABLE',
    'get_analytics_service', 'create_analytics_service', 'AnalyticsService',
    'ANALYTICS_SERVICE_AVAILABLE'
]
