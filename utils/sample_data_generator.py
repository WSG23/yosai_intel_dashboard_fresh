# utils/sample_data_generator.py
import logging
import random
import uuid
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def generate_sample_access_data(num_records: int = 1000) -> pd.DataFrame:
    """Generate sample access control data for testing"""

    # Sample data parameters
    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()

    # Sample users
    users = [f"EMP{str(i).zfill(4)}" for i in range(1, 51)]  # 50 employees
    visitors = [f"VIS{str(i).zfill(3)}" for i in range(1, 21)]  # 20 visitors
    all_people = users + visitors

    # Sample doors
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

    # Sample access results
    access_results = ["Granted", "Denied", "Timeout", "Error"]
    access_weights = [0.8, 0.15, 0.03, 0.02]  # Most access granted

    # Generate data
    data = []

    for i in range(num_records):
        # Random timestamp
        random_date = start_date + timedelta(
            seconds=random.randint(0, int((end_date - start_date).total_seconds()))
        )

        # Business hours bias (more activity during 8 AM - 6 PM)
        if random.random() < 0.7:  # 70% during business hours
            business_start = random_date.replace(hour=8, minute=0, second=0)
            business_end = random_date.replace(hour=18, minute=0, second=0)
            random_date = business_start + timedelta(
                seconds=random.randint(
                    0, int((business_end - business_start).total_seconds())
                )
            )

        # Select person (visitors less frequent)
        if random.random() < 0.8:
            person_id = random.choice(users)
        else:
            person_id = random.choice(visitors)

        # Select door
        door_id = random.choice(doors)

        # Access result (different probabilities for different doors)
        if door_id in ["SERVER_ROOM_A", "EXECUTIVE_FLOOR", "CLEAN_ROOM"]:
            # Critical doors - more denials
            access_result = np.random.choice(access_results, p=[0.6, 0.35, 0.03, 0.02])
        else:
            # Regular doors - mostly granted
            access_result = np.random.choice(access_results, p=access_weights)

        # Badge status
        if access_result == "Denied":
            badge_status = random.choice(["Invalid", "Expired", "Suspended"])
        else:
            badge_status = "Valid"

        # Other fields
        event_id = str(uuid.uuid4())
        badge_id = f"BADGE_{person_id}"
        door_held_time = random.uniform(0.5, 5.0) if access_result == "Granted" else 0.0
        entry_without_badge = random.random() < 0.02  # 2% chance

        data.append(
            {
                "event_id": event_id,
                "timestamp": random_date,
                "person_id": person_id,
                "door_id": door_id,
                "badge_id": badge_id,
                "access_result": access_result,
                "badge_status": badge_status,
                "door_held_open_time": round(door_held_time, 2),
                "entry_without_badge": entry_without_badge,
                "device_status": "normal",
            }
        )

    df = pd.DataFrame(data)
    df = df.sort_values("timestamp").reset_index(drop=True)

    return df


def save_sample_data() -> None:
    # Generate different sized datasets
    datasets = {
        "sample_small.csv": 100,
        "sample_medium.csv": 1000,
        "sample_large.csv": 10000,
    }

    for filename, size in datasets.items():
        df = generate_sample_access_data(size)

        # Save as CSV
        df.to_csv(f"data/{filename}", index=False)

        # Save as JSON
        json_filename = filename.replace(".csv", ".json")
        df.to_json(f"data/{json_filename}", orient="records", date_format="iso")

        # Save as Excel
        excel_filename = filename.replace(".csv", ".xlsx")
        df.to_excel(f"data/{excel_filename}", index=False)

        logger.info(f"Generated {filename}: {len(df)} records")


if __name__ == "__main__":
    # Create data directory
    import os

    os.makedirs("data", exist_ok=True)

    # Generate sample data
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


def test_file_upload() -> bool:
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
