import random
import time
import uuid
from datetime import datetime


class PerformanceTestRunner:
    """Simple event processing performance benchmark."""

    def __init__(self, num_events: int = 10000):
        self.num_events = num_events

    def _generate_event(self) -> dict:
        return {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow(),
            "value": random.random(),
        }

    def process_event(self, event: dict) -> None:
        # Placeholder for real event processing logic
        _ = event["event_id"]

    def run(self) -> float:
        start = time.perf_counter()
        for _ in range(self.num_events):
            event = self._generate_event()
            self.process_event(event)
        end = time.perf_counter()
        total = end - start
        print(f"Processed {self.num_events} events in {total:.2f} seconds")
        return total


if __name__ == "__main__":
    runner = PerformanceTestRunner()
    runner.run()
