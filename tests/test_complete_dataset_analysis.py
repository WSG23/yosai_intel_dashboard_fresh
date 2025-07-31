#!/usr/bin/env python3
"""Test complete dataset analysis without row limits."""

import os
import tempfile

import pandas as pd
import pytest

from yosai_intel_dashboard.src.services.analytics_service import AnalyticsService


def test_complete_dataset_analysis():
    """Test that analytics processes complete dataset, not just samples."""

    # Create test dataset with 2500 rows (more than typical limits)
    test_data = []
    for i in range(2500):
        test_data.append(
            {
                "person_id": f"USER_{i % 100}",
                "door_id": f"DOOR_{i % 50}",
                "access_result": "Granted" if i % 3 != 0 else "Denied",
                "timestamp": f"2024-01-{(i % 30) + 1:02d} {(i % 24):02d}:00:00",
            }
        )

    df = pd.DataFrame(test_data)

    # Save to temporary CSV
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        df.to_csv(f.name, index=False)
        temp_path = f.name

    try:
        service = AnalyticsService()

        uploaded_data = {"test_file.csv": temp_path}

        result = service._process_uploaded_data_directly(uploaded_data)

        assert (
            result["total_events"] == 2500
        ), f"Expected 2500 events, got {result['total_events']}"
        assert (
            result["active_users"] == 100
        ), f"Expected 100 users, got {result['active_users']}"
        assert (
            result["active_doors"] == 50
        ), f"Expected 50 doors, got {result['active_doors']}"
        assert result["status"] == "success"

    finally:
        os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__])
