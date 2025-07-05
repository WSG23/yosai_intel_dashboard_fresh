"""Unified callback controller re-exported under the core package."""

from callback_controller import (
    CallbackEvent,
    CallbackContext,
    CallbackProtocol,
    CallbackRegistry,
    CallbackController,
    callback_handler,
    TemporaryCallback,
    get_callback_controller,
    fire_event,
)

__all__ = [
    "CallbackEvent",
    "CallbackContext",
    "CallbackProtocol",
    "CallbackRegistry",
    "CallbackController",
    "callback_handler",
    "TemporaryCallback",
    "get_callback_controller",
    "fire_event",
]