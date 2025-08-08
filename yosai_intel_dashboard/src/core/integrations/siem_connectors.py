"""Connectors for pushing events to common SIEM systems."""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


logger = logging.getLogger(__name__)


def send_to_siem(event: Dict, system: str) -> None:
    """Send an ``event`` to a named SIEM ``system``.

    The implementation is deliberately generic and logs the payload.  Real
    connectors would authenticate and forward the event using the vendor's API.
    """

    if system.lower() not in {"splunk", "qradar", "elk"}:
        raise ValueError(f"Unknown SIEM system: {system}")
    # In real code this would send the event. For now we simply emit a log so
    # tests and examples can observe the behaviour without side effects.
    logger.info("Sending event to %s: %s", system, event)
