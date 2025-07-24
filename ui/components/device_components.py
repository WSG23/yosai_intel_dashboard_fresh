"""Wrapper functions for device mapping UI components."""

from __future__ import annotations

from typing import List

import dash_bootstrap_components as dbc
from dash import html

from components.simple_device_mapping import (
    create_device_mapping_section as _create_section,
)
from components.simple_device_mapping import (
    create_simple_device_modal_with_ai as _create_modal_ai,
)


def create_simple_device_modal_with_ai(devices: List[str]) -> dbc.Modal:
    return _create_modal_ai(devices)


def create_device_mapping_section(devices: List[str] | None = None) -> html.Div:
    return _create_section(devices)
