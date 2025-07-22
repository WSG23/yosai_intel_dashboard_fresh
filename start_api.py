#!/usr/bin/env python
import sys
import os
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import Flask app directly from adapter
import api.adapter
from config.constants import API_PORT
from tracing import init_tracing

logger = logging.getLogger("start")
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter(
        '{"time":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}'
    )
)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def main() -> None:
    """Start the API development server."""
    init_tracing("api")
    app = api.adapter.app


    logger.info("Starting Yosai Intel Dashboard API", extra={"port": API_PORT})
    logger.info(
        "Health check", extra={"url": f"http://localhost:{API_PORT}/api/v1/health"}
    )

    app.run(host="0.0.0.0", port=API_PORT, debug=True)


if __name__ == "__main__":
    main()
