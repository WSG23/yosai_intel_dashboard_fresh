from __future__ import annotations

import logging

import pytest

from src.common.base import BaseComponent
from src.common.mixins import (
    Loggable,
    LoggingMixin,
    Serializable,
    SerializationMixin,
)


class DummyLoggingComponent(LoggingMixin, BaseComponent):
    def __init__(self) -> None:
        super().__init__()


class DummySerializationComponent(SerializationMixin, BaseComponent):
    def __init__(self, value: int, component_id: str | None = None) -> None:
        super().__init__(component_id)
        self.value = value


def test_logging_mixin_logs(caplog):
    comp = DummyLoggingComponent()
    assert isinstance(comp, Loggable)
    with caplog.at_level(logging.INFO):
        comp.log("hello world")
    assert "hello world" in caplog.text


def test_logging_mixin_custom_level(caplog):
    comp = DummyLoggingComponent()
    with caplog.at_level(logging.DEBUG):
        comp.log("debug msg", logging.DEBUG)
    assert "debug msg" in caplog.text


def test_serialization_mixin_roundtrip():
    comp = DummySerializationComponent(5)
    assert isinstance(comp, Serializable)
    data = comp.to_dict()
    assert data["value"] == 5
    new_comp = DummySerializationComponent.from_dict(data)
    assert isinstance(new_comp, DummySerializationComponent)
    assert new_comp.value == 5
