"""Central callback registration for dashboard pages.

Ingress: consumes user interactions and service events.
Egress: emits UI updates and invokes service-layer calls via callbacks.
"""

from .controller import (
    register_callbacks,
    register_greetings_callbacks,
    register_upload_callbacks,
    register_device_learning_callbacks,
)

__all__ = [
    "register_callbacks",
    "register_greetings_callbacks",
    "register_upload_callbacks",
    "register_device_learning_callbacks",
]
