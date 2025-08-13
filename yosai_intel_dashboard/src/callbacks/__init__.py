"""Callback registration helpers."""

from .controller import (
    CallbackIds,
    DeviceLearningIds,
    GreetingIds,
    UploadIds,
    register_callbacks,
    register_device_learning_callbacks,
    register_greeting_callbacks,
    register_upload_callbacks,
)

__all__ = [
    "CallbackIds",
    "DeviceLearningIds",
    "GreetingIds",
    "UploadIds",
    "register_callbacks",
    "register_device_learning_callbacks",
    "register_greeting_callbacks",
    "register_upload_callbacks",
]
