from typing import Any, Callable, Dict, List, Tuple, cast

from unittest import mock
import pytest
import dash

from components.column_verification import (
    register_callbacks as register_column_callbacks,
)
from components.column_verification import (
    toggle_custom_field as toggle_custom_field_untyped,
)
from components.device_verification import mark_device_as_edited as mark_device_as_edited_untyped
from components.simple_device_mapping import (
    apply_ai_device_suggestions as apply_ai_device_suggestions_untyped,
)
from components.simple_device_mapping import (
    register_callbacks as register_device_callbacks,
)

pytestmark = pytest.mark.usefixtures("fake_dash")

# Cast imported helpers so mypy treats them as typed callables. The actual
# implementations are untyped in the source code which would otherwise trigger
# "no-untyped-call" errors when called from these tests.
toggle_custom_field = cast(
    Callable[[str | None], Dict[str, str]], toggle_custom_field_untyped
)
apply_ai_device_suggestions = cast(
    Callable[[Dict[str, Dict[str, Any]], List[str]], Tuple[Any, Any, Any, Any]],
    apply_ai_device_suggestions_untyped,
)
mark_device_as_edited = cast(
    Callable[[Any, Any, Any, Any], bool], mark_device_as_edited_untyped
)


def test_toggle_custom_field() -> None:
    assert toggle_custom_field("other") == {"display": "block"}
    assert toggle_custom_field("person_id") == {"display": "none"}
    assert toggle_custom_field(None) == {"display": "none"}


def test_apply_ai_device_suggestions_basic() -> None:
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


def test_apply_ai_device_suggestions_empty() -> None:
    result = apply_ai_device_suggestions({}, [])
    assert result == (dash.no_update, dash.no_update, dash.no_update, dash.no_update)


def test_mark_device_as_edited() -> None:
    assert mark_device_as_edited(None, None, None, None) is True


def test_register_callbacks_invoked() -> None:
    manager = mock.Mock()

    def fake_register(*args: Any, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            # record registration details for assertion without type errors
            setattr(decorator, "called_with", kwargs.get("callback_id"))
            setattr(decorator, "func", func)
            return func

        return decorator

    manager.register_callback.side_effect = fake_register
    register_column_callbacks(manager)
    register_device_callbacks(manager)

    calls = [c.kwargs.get("callback_id") for c in manager.register_callback.mock_calls]
    assert "toggle_custom_field" in calls
    assert "apply_ai_device_suggestions" in calls
    assert "populate_simple_device_modal" in calls
