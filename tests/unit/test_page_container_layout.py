import re
from importlib import import_module

from dash import dcc, html, page_container

# Import _create_main_layout directly from the app factory module
layout_module = import_module("core.app_factory")
create_main_layout = layout_module._create_main_layout


def test_page_container_in_layout():
    layout = create_main_layout()
    assert "page_container" in str(layout)
