#!/usr/bin/env python3
"""Basic streaming producer for testing event ingestion."""

import json
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from yosai_intel_dashboard.src.services.streaming import StreamingService


def main() -> None:
    service = StreamingService()
    service.initialize()
    try:
        for i in range(10):
            payload = {"message": f"test-{i}", "timestamp": time.time()}
            service.publish(json.dumps(payload).encode("utf-8"))
            print(f"sent {payload}")
            time.sleep(1)
    finally:
        service.close()


if __name__ == "__main__":
    main()
