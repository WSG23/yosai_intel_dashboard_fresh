from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def mock_db_connection():
    conn = mock.Mock()
    conn.health_check.return_value = True
    return conn
