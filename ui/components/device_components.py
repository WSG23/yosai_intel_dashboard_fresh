"""Wrapper functions for device mapping UI components."""

from __future__ import annotations

from typing import List

from dash import html
import dash_bootstrap_components as dbc

from components.simple_device_mapping import (
    create_simple_device_modal_with_ai as _create_modal_ai,
    create_device_mapping_section as _create_section,
)


def create_simple_device_modal_with_ai(devices: List[str]) -> dbc.Modal:
    return _create_modal_ai(devices)


def create_device_mapping_section(devices: List[str] | None = None) -> html.Div:
    return _create_section(devices)
