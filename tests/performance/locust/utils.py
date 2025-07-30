import random
import string
import time
from dataclasses import dataclass
from typing import Dict, List

EVENT_TYPES: List[str] = ["granted", "denied", "tailgating", "forced"]


def random_user_id() -> str:
    """Return a random user identifier."""
    return "user-" + "".join(
        random.choices(string.ascii_lowercase + string.digits, k=8)
    )


def generate_event() -> Dict[str, str]:
    """Generate a single random event record."""
    return {
        "user_id": random_user_id(),
        "device_id": f"device-{random.randint(1, 100):03d}",
        "event_type": random.choice(EVENT_TYPES),
        "timestamp": int(time.time() * 1000),
    }
