"""Centralised test configuration helpers.

This module aggregates commonly used test configuration objects so that tests
can import from ``tests.config`` instead of scattered modules.
"""
from tests.fake_configuration import FakeConfiguration
from tests.stubs.config.config import Dummy, get_config, get_analytics_config

__all__ = ["FakeConfiguration", "Dummy", "get_config", "get_analytics_config"]

