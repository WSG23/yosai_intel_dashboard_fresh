from __future__ import annotations

from yosai_intel_dashboard.src.core.env_validation import validate_required_env
from yosai_intel_dashboard.src.core.app_factory import create_app
from yosai_intel_dashboard.src.core.logging import get_logger

validate_required_env()

app = create_app()
server = app.server

logger = get_logger(__name__)

if __name__ == "__main__":
    import os
    import sys

    dev_mode = os.environ.get("YOSAI_DEV") == "1" or "--dev" in sys.argv
    if dev_mode:
        app.run()
    else:
        logger.error(
            "Refusing to start the development server without development mode",
            extra={"dev_mode": dev_mode},
        )
