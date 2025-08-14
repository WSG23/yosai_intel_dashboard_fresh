try:
    from yosai_intel_dashboard.src.infrastructure.monitoring.logging_utils import get_logger
except Exception:
    import logging
    def get_logger(name: str):
        logger = logging.getLogger(name)
        if not logger.handlers:
            logging.basicConfig(level=logging.INFO)
        return logger
