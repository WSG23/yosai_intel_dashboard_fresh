import pytest
import dash_bootstrap_components as dbc
from dash import dcc, html

pytestmark = pytest.mark.usefixtures("fake_dash", "fake_dbc")

from components.column_verification import create_column_verification_modal
from components.device_verification import (
    create_device_verification_modal,
    toggle_device_verification_modal,
)


def _collect(component, cls):
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


def test_create_column_verification_modal_basic():
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


def test_create_column_verification_modal_empty():
    modal = create_column_verification_modal({"filename": "x.csv", "columns": []})
    assert isinstance(modal, html.Div)


def test_create_device_verification_modal_basic():
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


def test_create_device_verification_modal_empty():
    modal = create_device_verification_modal({}, "sess")
    assert isinstance(modal, html.Div)


def test_toggle_device_verification_modal():
    # Opens when triggered from a closed state
    assert toggle_device_verification_modal(1, None, False) is True
    # Closes when either button is pressed while open
    assert toggle_device_verification_modal(None, 1, True) is False
