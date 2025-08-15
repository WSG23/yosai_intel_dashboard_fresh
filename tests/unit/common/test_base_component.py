from __future__ import annotations

from src.common.base import BaseComponent


def test_default_component_id():
    comp = BaseComponent()
    assert comp.component_id == "BaseComponent"


def test_custom_component_id():
    comp = BaseComponent("custom")
    assert comp.component_id == "custom"
