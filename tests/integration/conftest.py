from __future__ import annotations

import pytest

from tests.conftest import kafka_service, postgres_service  # re-export fixtures

pytestmark = pytest.mark.slow

__all__ = ["kafka_service", "postgres_service"]
