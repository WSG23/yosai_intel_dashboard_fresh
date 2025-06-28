#!/usr/bin/env python3
"""
Core package initialization - Fixed for streamlined architecture
"""
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import the main app factory function (only what exists)
from .app_factory import create_app

__all__ = ['create_app']
