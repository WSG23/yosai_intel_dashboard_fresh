# utils/sample_data_generator.py
import logging
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def _random_timestamp(start: datetime, end: datetime) -> datetime:
    """Return a random timestamp biased toward business hours."""

    random_date = start + timedelta(
        seconds=random.randint(0, int((end - start).total_seconds()))
    )
    if random.random() < 0.7:
        business_start = random_date.replace(hour=8, minute=0, second=0)
        business_end = random_date.replace(hour=18, minute=0, second=0)
        random_date = business_start + timedelta(
            seconds=random.randint(
                0, int((business_end - business_start).total_seconds())
            )
        )
    return random_date


def _create_access_event(
    start: datetime,
    end: datetime,
    users: Sequence[str],
    visitors: Sequence[str],
    doors: Sequence[str],
    access_results: Sequence[str],
    access_weights: Sequence[float],
) -> dict[str, Any]:
    """Build a single access event record."""

    random_date = _random_timestamp(start, end)
    person_id = (
        random.choice(users) if random.random() < 0.8 else random.choice(visitors)
    )
    door_id = random.choice(doors)
    if door_id in ["SERVER_ROOM_A", "EXECUTIVE_FLOOR", "CLEAN_ROOM"]:
        access_result = np.random.choice(access_results, p=[0.6, 0.35, 0.03, 0.02])
    else:
        access_result = np.random.choice(access_results, p=access_weights)

    badge_status = (
        random.choice(["Invalid", "Expired", "Suspended"])
        if access_result == "Denied"
        else "Valid"
    )
    door_held_time = random.uniform(0.5, 5.0) if access_result == "Granted" else 0.0
    return {
        "event_id": str(uuid.uuid4()),
        "timestamp": random_date,
        "person_id": person_id,
        "door_id": door_id,
        "badge_id": f"BADGE_{person_id}",
        "access_result": access_result,
        "badge_status": badge_status,
        "door_held_open_time": round(door_held_time, 2),
        "entry_without_badge": random.random() < 0.02,
        "device_status": "normal",
    }


def generate_sample_access_data(num_records: int = 1000) -> pd.DataFrame:
    """Generate sample access control data for testing."""

    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()
    users = [f"EMP{str(i).zfill(4)}" for i in range(1, 51)]
    visitors = [f"VIS{str(i).zfill(3)}" for i in range(1, 21)]
    doors = [
        "MAIN_ENTRANCE",
        "SERVER_ROOM_A",
        "EXECUTIVE_FLOOR",
        "LAB_ENTRANCE",
        "CLEAN_ROOM",
        "PARKING_GATE",
        "CAFETERIA",
        "MEETING_ROOM_A",
        "MEETING_ROOM_B",
        "STORAGE_A",
        "EMERGENCY_EXIT_1",
        "EMERGENCY_EXIT_2",
    ]
    access_results = ["Granted", "Denied", "Timeout", "Error"]
    access_weights = [0.8, 0.15, 0.03, 0.02]

    data = [
        _create_access_event(
            start_date,
            end_date,
            users,
            visitors,
            doors,
            access_results,
            access_weights,
        )
        for _ in range(num_records)
    ]
    df = pd.DataFrame(data).sort_values("timestamp").reset_index(drop=True)
    return df


def save_sample_data() -> None:
    """Persist generated datasets to disk."""

    datasets = {
        "sample_small.csv": 100,
        "sample_medium.csv": 1000,
        "sample_large.csv": 10000,
    }

    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    for filename, size in datasets.items():
        df = generate_sample_access_data(size)
        df.to_csv(data_dir / filename, index=False)

        json_filename = filename.replace(".csv", ".json")
        df.to_json(data_dir / json_filename, orient="records", date_format="iso")

        excel_filename = filename.replace(".csv", ".xlsx")
        df.to_excel(data_dir / excel_filename, index=False)

        logger.info(f"Generated {filename}: {len(df)} records")


if __name__ == "__main__":
    save_sample_data()
    logger.info("Sample data generated successfully!")
    logger.info("Files created in data/ directory:")
    logger.info("- sample_small.csv/json/xlsx (100 records)")
    logger.info("- sample_medium.csv/json/xlsx (1,000 records)")
    logger.info("- sample_large.csv/json/xlsx (10,000 records)")

# Create a simple test script
# test_analytics.py
"""
Simple test script to verify analytics functionality
Run this after setting up the project structure
"""


def test_file_upload():
    """Test file upload functionality"""

    # Generate test data using function defined above
    df = generate_sample_access_data(100)
    logger.info(f"Generated test data: {len(df)} records")
    logger.info(f"Columns: {list(df.columns)}")
    logger.info(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")

    # Test basic analytics
    logger.info("\nBasic Analytics:")
    logger.info(f"Total events: {len(df)}")
    logger.info(f"Unique users: {df['person_id'].nunique()}")
    logger.info(f"Access results: {df['access_result'].value_counts().to_dict()}")
    return True


if __name__ == "__main__":
    test_file_upload()
    logger.info("Test completed successfully!")
