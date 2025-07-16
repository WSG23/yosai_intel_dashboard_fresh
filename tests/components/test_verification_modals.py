import pytest
import dash_bootstrap_components as dbc
from dash import dcc, html

pytestmark = pytest.mark.usefixtures("fake_dash", "fake_dbc")

from typing import Any, Callable, List, cast

from components.column_verification import create_column_verification_modal as create_column_verification_modal_untyped
from components.device_verification import (
    create_device_verification_modal as create_device_verification_modal_untyped,
    toggle_device_verification_modal as toggle_device_verification_modal_untyped,
)

# Provide typed wrappers for imported helpers
create_column_verification_modal = cast(
    Callable[[dict[str, Any]], Any], create_column_verification_modal_untyped
)
create_device_verification_modal = cast(
    Callable[[dict[str, Any], str], Any], create_device_verification_modal_untyped
)
toggle_device_verification_modal = cast(
    Callable[[Any, Any, bool], bool], toggle_device_verification_modal_untyped
)


def _collect(component: Any, cls: type[Any]) -> List[Any]:
    """Recursively collect components of a given class."""
    found = []
    if isinstance(component, cls):
        found.append(component)
    children = getattr(component, "children", None)
    if isinstance(children, (list, tuple)):
        for c in children:
            found.extend(_collect(c, cls))
    elif children is not None:
        found.extend(_collect(children, cls))
    return found


def test_create_column_verification_modal_basic() -> None:
    info = {
        "filename": "sample.csv",
        "columns": ["User", "Door"],
        "ai_suggestions": {
            "User": {"field": "person_id", "confidence": 0.9},
            "Door": {"field": "door_id", "confidence": 0.8},
        },
    }
    modal = create_column_verification_modal(info)
    assert isinstance(modal, dbc.Modal)
    assert modal.id == "column-verification-modal"
    dropdowns = _collect(modal, dcc.Dropdown)
    assert len(dropdowns) >= len(info["columns"])
    header = _collect(modal, html.H5)[0]
    assert "sample.csv" in "".join(str(c) for c in header.children)


def test_create_column_verification_modal_empty() -> None:
    modal = create_column_verification_modal({"filename": "x.csv", "columns": []})
    assert isinstance(modal, html.Div)


def test_create_device_verification_modal_basic() -> None:
    mappings = {
        "door1": {"floor_number": 1, "is_entry": True, "confidence": 0.8},
        "door2": {"floor_number": 2, "is_exit": True, "confidence": 0.6},
    }
    modal = create_device_verification_modal(mappings, "sess")
    assert isinstance(modal, dbc.Modal)
    assert modal.id == "device-verification-modal"
    rows = _collect(modal, html.Tr)
    # subtract header row
    assert len(rows) - 1 == len(mappings)


def test_create_device_verification_modal_empty() -> None:
    modal = create_device_verification_modal({}, "sess")
    assert isinstance(modal, html.Div)


def test_toggle_device_verification_modal() -> None:
    # Opens when triggered from a closed state
    assert toggle_device_verification_modal(1, None, False) is True
    # Closes when either button is pressed while open
    assert toggle_device_verification_modal(None, 1, True) is False
