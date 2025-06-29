"""Tests for the upload page."""

from pathlib import Path
import csv

import pytest

from core.app_factory import create_app


@pytest.fixture()
def sample_csv(tmp_path: Path) -> Path:
    """Create a temporary CSV file for upload testing."""

    test_data = [
        ["device_name", "user_name", "timestamp", "access_type"],
        ["Door_A1", "John_Smith", "2025-06-28 10:00:00", "entry"],
        ["Door_B2", "Jane_Doe", "2025-06-28 10:05:00", "exit"],
        ["Door_C3", "Bob_Wilson", "2025-06-28 10:10:00", "entry"],
        ["Door_A1", "Alice_Brown", "2025-06-28 10:15:00", "exit"],
        ["Door_D4", "Mike_Davis", "2025-06-28 10:20:00", "entry"],
    ]

    file_path = tmp_path / "test_upload_data.csv"
    with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(test_data)

    return file_path


def test_sample_csv_created(sample_csv: Path) -> None:
    """Verify the temporary CSV contains the expected rows."""

    with open(sample_csv, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    # header + 5 data rows
    assert len(rows) == 6


def test_upload_page_renders(dash_duo) -> None:
    """Ensure the upload page renders and the upload component exists."""

    app = create_app()
    dash_duo.start_server(app)

    dash_duo.driver.get(dash_duo.server_url + "/upload")
    upload = dash_duo.find_element("#upload-data")

    assert upload is not None
