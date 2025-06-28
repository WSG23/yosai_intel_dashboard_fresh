"""Test configuration and fixtures"""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Generator
import pandas as pd

from core.container import Container
from models.entities import Person, Door, AccessEvent
from models.enums import AccessResult, DoorType


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create temporary directory for tests"""

    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def di_container() -> Container:
    """Create DI container for tests"""

    return Container()


@pytest.fixture
def sample_access_data() -> pd.DataFrame:
    """Sample access data for testing"""

    return pd.DataFrame(
        [
            {
                "person_id": "EMP001",
                "door_id": "MAIN_ENTRANCE",
                "timestamp": "2024-01-15 09:00:00",
                "access_result": AccessResult.GRANTED.value,
            },
            {
                "person_id": "EMP002",
                "door_id": "SERVER_ROOM",
                "timestamp": "2024-01-15 23:00:00",
                "access_result": AccessResult.DENIED.value,
            },
        ]
    )


@pytest.fixture
def sample_persons() -> list[Person]:
    """Sample person entities for testing"""

    return [
        Person(
            person_id="EMP001",
            name="John Doe",
            department="IT",
            clearance_level=3,
        ),
        Person(
            person_id="EMP002",
            name="Jane Smith",
            department="Security",
            clearance_level=5,
        ),
    ]


@pytest.fixture
def sample_doors() -> list[Door]:
    """Sample door entities for testing"""

    return [
        Door(
            door_id="MAIN_ENTRANCE",
            door_name="Main Entrance",
            facility_id="HQ",
            area_id="LOBBY",
            door_type=DoorType.STANDARD,
        ),
        Door(
            door_id="SERVER_ROOM",
            door_name="Server Room",
            facility_id="HQ",
            area_id="IT_FLOOR",
            door_type=DoorType.CRITICAL,
            required_clearance=4,
        ),
    ]

