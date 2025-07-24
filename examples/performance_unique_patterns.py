#!/usr/bin/env python3
"""Measure execution time of get_unique_patterns_analysis."""

import logging
import random
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from services.analytics_service import AnalyticsService


def generate_sample_access_data(num_records: int = 1000):
    """Generate realistic access control data"""
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

    data = []
    for _ in range(num_records):
        random_date = start_date + timedelta(
            seconds=random.randint(0, int((end_date - start_date).total_seconds()))
        )
        if random.random() < 0.7:
            business_start = random_date.replace(hour=8, minute=0, second=0)
            business_end = random_date.replace(hour=18, minute=0, second=0)
            random_date = business_start + timedelta(
                seconds=random.randint(0, int((business_end - business_start).total_seconds()))
            )
        person_id = random.choice(users) if random.random() < 0.8 else random.choice(visitors)
        door_id = random.choice(doors)
        if door_id in ["SERVER_ROOM_A", "EXECUTIVE_FLOOR", "CLEAN_ROOM"]:
            access_result = np.random.choice(access_results, p=[0.6, 0.35, 0.03, 0.02])
        else:
            access_result = np.random.choice(access_results, p=access_weights)
        badge_status = random.choice(["Invalid", "Expired", "Suspended"]) if access_result == "Denied" else "Valid"
        door_held_time = random.uniform(0.5, 5.0) if access_result == "Granted" else 0.0
        data.append(
            {
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
        )
    df = pd.DataFrame(data).sort_values("timestamp").reset_index(drop=True)
    return df

logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Generating sample dataset...")
    df = generate_sample_access_data(5000)
    service = AnalyticsService()
    service.upload_processor.load_uploaded_data = lambda: {"sample.csv": df}
    start = perf_counter()
    result = service.get_unique_patterns_analysis()
    elapsed = perf_counter() - start

    logger.info("Analysis status: %s", result.get("status"))
    logger.info("Elapsed time: %.3f seconds", elapsed)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    main()
