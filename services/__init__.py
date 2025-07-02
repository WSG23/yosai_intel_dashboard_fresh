#!/usr/bin/env python3
"""Simplified Services Package"""
import logging

from .ai_mapping_store import ai_mapping_store
from .data_loader import DataLoader
from .data_validation import DataValidationService
from .analytics_generator import AnalyticsGenerator
from .data_loading_service import DataLoadingService
from .registry import get_service

logger = logging.getLogger(__name__)

# Resolve optional services from the registry
FileProcessor = get_service("FileProcessor")
FILE_PROCESSOR_AVAILABLE = FileProcessor is not None

get_analytics_service = get_service("get_analytics_service")
create_analytics_service = get_service("create_analytics_service")
AnalyticsService = get_service("AnalyticsService")
ANALYTICS_SERVICE_AVAILABLE = AnalyticsService is not None

__all__ = [
    "FileProcessor",
    "FILE_PROCESSOR_AVAILABLE",
    "get_analytics_service",
    "create_analytics_service",
    "AnalyticsService",
    "ANALYTICS_SERVICE_AVAILABLE",
    "DataLoader",
    "DataValidationService",
    "AnalyticsGenerator",
    "DataLoadingService",
    "ai_mapping_store",
]
