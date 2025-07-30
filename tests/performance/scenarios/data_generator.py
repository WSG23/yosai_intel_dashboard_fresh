"""Generate realistic event data based on traffic patterns."""

from __future__ import annotations

import random
import time
from pathlib import Path
from typing import Dict, List

import yaml

from ..locust.utils import EVENT_TYPES, random_user_id


def load_pattern(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def generate_events(pattern_file: str, count: int) -> List[Dict]:
    pattern = load_pattern(pattern_file)
    mix = pattern.get("mix", {})
    weights = [mix.get(t, 0.0) for t in EVENT_TYPES]
    events = []
    for _ in range(count):
        events.append(
            {
                "user_id": random_user_id(),
                "device_id": f"device-{random.randint(1, 100):03d}",
                "event_type": random.choices(EVENT_TYPES, weights=weights, k=1)[0],
                "timestamp": int(time.time() * 1000),
            }
        )
    return events


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser()
    parser.add_argument("pattern", help="YAML pattern file")
    parser.add_argument("count", type=int, default=1000)
    parser.add_argument("output", type=Path, default=Path("events.json"))
    args = parser.parse_args()

    data = generate_events(args.pattern, args.count)
    with args.output.open("w", encoding="utf-8") as fh:
        json.dump(data, fh)
    print(f"Generated {args.count} events to {args.output}")
