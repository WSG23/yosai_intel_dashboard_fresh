import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "stubs"))

from yosai_intel_dashboard.src.infrastructure.logging.setup import LoggingService


def test_logging_service_sanitizes_surrogates(caplog):
    service = LoggingService()
    with caplog.at_level(logging.INFO, logger="yosai"):
        service.log_info("bad\ud83dmsg", detail="x\ud83d")

    record = caplog.records[0]
    assert record.getMessage() == "badmsg"
    assert record.detail == "x"
