from __future__ import annotations
import os, sys
try:
    from yosai_intel_dashboard.src.infrastructure.monitoring.logging_utils import get_logger
except Exception:
    import logging
    def get_logger(name: str):
        logger = logging.getLogger(name)
        if not logger.handlers:
            logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
        return logger
from fastapi import FastAPI
app = FastAPI()
logger = get_logger(__name__)
@app.get("/health")
def health():
    return {"status": "ok"}
from fastapi.responses import RedirectResponse

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/docs")
