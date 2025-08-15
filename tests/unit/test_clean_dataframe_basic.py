from __future__ import annotations

from datetime import datetime
import pytest
import sys
from pathlib import Path
import tests.infrastructure as infra_mod

from tests.infrastructure import MockFactory, TestInfrastructure


@pytest.fixture(scope="module")
def factory() -> MockFactory:
    with TestInfrastructure(MockFactory(), stub_packages=[]) as f:
        stubs_path = Path(infra_mod.__file__).resolve().parents[1] / "stubs"
        if str(stubs_path) in sys.path:
            sys.path.remove(str(stubs_path))
        yield f


def test_clean_uploaded_dataframe_maps_columns_and_parses_timestamp(
    factory: MockFactory,
) -> None:
    df = factory.dataframe(
        {
            "Timestamp": ["2024-01-01 00:00:00"],
            "Person ID": ["u1"],
            "Token ID": ["t1"],
            "Device name": ["d1"],
            "Access result": ["Granted"],
        }
    )
    ua = factory.upload_processor()
    cleaned = ua.clean_uploaded_dataframe(df)
    assert cleaned.columns.tolist() == [
        "timestamp",
        "person_id",
        "token_id",
        "door_id",
        "access_result",
    ]
    assert isinstance(cleaned["timestamp"][0], datetime)


def test_clean_uploaded_dataframe_drops_empty_rows_and_columns(
    factory: MockFactory,
) -> None:
    df = factory.dataframe(
        {
            "Timestamp": ["2024-01-01 00:00:00", None],
            "Person ID": ["u1", None],
            "Token ID": ["t1", None],
            "Device name": ["d1", None],
            "Access result": ["Granted", None],
            "EmptyCol": [None, None],
        }
    )
    ua = factory.upload_processor()
    cleaned = ua.clean_uploaded_dataframe(df)
    assert cleaned.columns.tolist() == [
        "timestamp",
        "person_id",
        "token_id",
        "door_id",
        "access_result",
    ]
    assert len(cleaned) == 1


