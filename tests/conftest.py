"""Pytest configuration for the test-suite."""
from __future__ import annotations

import importlib.util
import warnings
import pytest

import pytest

pytest_plugins = ["tests.config"]


_missing_packages = [
    pkg for pkg in ("yaml", "psutil") if importlib.util.find_spec(pkg) is None
]
if _missing_packages:
    warnings.warn(
        "Missing required test dependencies: " + ", ".join(_missing_packages),
        RuntimeWarning,
    )


@pytest.fixture
def temp_dir(tmp_path_factory):
    """Provide a temporary directory unique to each test."""
    return tmp_path_factory.mktemp("tmp")


@pytest.fixture
def di_container():
    """Simple dependency injection container instance."""
    from yosai_intel_dashboard.src.infrastructure.di.service_container import ServiceContainer

    return ServiceContainer()


@pytest.fixture
def fake_unicode_processor():
    """Fixture returning a ``FakeUnicodeProcessor`` instance."""
    from .fake_unicode_processor import FakeUnicodeProcessor

    return FakeUnicodeProcessor()
