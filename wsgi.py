from __future__ import annotations
import os, sys
try:
    from yosai_intel_dashboard.src.infrastructure.monitoring.logging_utils import get_logger
except Exception:
    import logging
    def get_logger(name: str):
        logger = logging.getLogger(name)
        if not logger.handlers:
            logging.basicConfig(level=logging.INFO)
        return logger
logger = get_logger(__name__)
dev_mode = os.environ.get("YOSAI_DEV") == "1" or "--dev" in sys.argv
if dev_mode:
    from yosai_intel_dashboard.src.core.app_factory import create_app as _create_app
    application = _create_app()
else:
    from yosai_intel_dashboard.src.adapters.api.adapter import create_api_app
    application = create_api_app()
