from unittest import mock

import dash

from components.column_verification import (
    register_callbacks as register_column_callbacks,
)
from components.column_verification import (
    toggle_custom_field,
)
from components.device_verification import mark_device_as_edited
from components.simple_device_mapping import (
    apply_ai_device_suggestions,
)
from components.simple_device_mapping import (
    register_callbacks as register_device_callbacks,
)


def test_toggle_custom_field():
    assert toggle_custom_field("other") == {"display": "block"}
    assert toggle_custom_field("person_id") == {"display": "none"}
    assert toggle_custom_field(None) == {"display": "none"}


def test_apply_ai_device_suggestions_basic():
    suggestions = {
        "door1": {"floor_number": 1, "security_level": 2, "is_entry": True},
        "door2": {"floor_number": 2, "security_level": 4, "is_stairwell": True},
    }
    devices = ["door1", "door2"]
    floors, access, special, security = apply_ai_device_suggestions(
        suggestions, devices
    )
    assert floors == [1, 2]
    assert access == [["entry"], []]
    assert special == [[], ["is_stairwell"]]
    assert security == [2, 4]


def test_apply_ai_device_suggestions_empty():
    result = apply_ai_device_suggestions({}, [])
    assert result == (dash.no_update, dash.no_update, dash.no_update, dash.no_update)


def test_mark_device_as_edited():
    assert mark_device_as_edited(None, None, None, None) is True


def test_register_callbacks_invoked():
    manager = mock.Mock()

    def fake_register(*args, **kwargs):
        def decorator(func):
            decorator.called_with = kwargs.get("callback_id")
            decorator.func = func
            return func

        return decorator

    manager.register_callback.side_effect = fake_register
    register_column_callbacks(manager)
    register_device_callbacks(manager)

    calls = [c.kwargs.get("callback_id") for c in manager.register_callback.mock_calls]
    assert "toggle_custom_field" in calls
    assert "apply_ai_device_suggestions" in calls
