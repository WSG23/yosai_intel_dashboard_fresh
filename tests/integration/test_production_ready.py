from __future__ import annotations

import importlib
import types
import sys
from pathlib import Path

import pandas as pd
import pytest

from validation.security_validator import SecurityValidator
from yosai_intel_dashboard.src.core.events import EventBus
from yosai_intel_dashboard.src.infrastructure.callbacks.events import CallbackEvent
from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import (
    TrulyUnifiedCallbacks,
)
from yosai_intel_dashboard.src.infrastructure.config.dynamic_config import dynamic_config
from yosai_intel_dashboard.src.infrastructure.di.service_container import ServiceContainer

# Stub out heavy hashing dependency used during module import
hashing_stub = types.ModuleType("hashing")
hashing_stub.hash_dataframe = lambda df: "hash"
sys.modules.setdefault("yosai_intel_dashboard.src.utils.hashing", hashing_stub)

import importlib.util

module_path = (
    Path(__file__).resolve().parents[2]
    / "yosai_intel_dashboard"
    / "src"
    / "services"
    / "upload"
    / "upload_processing.py"
)
module_name = "yosai_intel_dashboard.src.services.upload.upload_processing"
spec = importlib.util.spec_from_file_location(module_name, module_path)
upload_module = importlib.util.module_from_spec(spec)
sys.modules[module_name] = upload_module
assert spec.loader is not None
spec.loader.exec_module(upload_module)
UploadAnalyticsProcessor = upload_module.UploadAnalyticsProcessor


class TestProductionReadiness:
    """High level tests exercising production critical paths."""

    def test_upload_to_analytics_pipeline(self) -> None:
        """Processing uploaded data should flow through analytics pipeline."""
        validator = SecurityValidator()
        class StubProcessor:
            pass
        processor = StubProcessor()
        event_bus = EventBus()
        callbacks = TrulyUnifiedCallbacks(
            event_bus=event_bus, security_validator=validator
        )
        upload_processor = UploadAnalyticsProcessor(
            validator, processor, callbacks, dynamic_config.analytics, event_bus
        )

        df = pd.DataFrame(
            {"Person ID": ["u1", "u2"], "Device name": ["d1", "d2"]}
        )
        upload_processor.load_uploaded_data = lambda: {"data.csv": df}
        result = upload_processor.analyze_uploaded_data()

        assert result["status"] == "success"
        assert result["rows"] == 2
        assert result["columns"] == 2

    def test_callback_registration_and_triggering(self) -> None:
        """Callbacks should register with correct names and be triggered."""
        manager = TrulyUnifiedCallbacks()
        events: list[int] = []

        def cb(val: int) -> None:
            events.append(val)

        manager.register_event(CallbackEvent.BEFORE_REQUEST, cb)
        manager.trigger_event(CallbackEvent.BEFORE_REQUEST, 1)

        registered = manager.get_event_callbacks(CallbackEvent.BEFORE_REQUEST)[0]
        assert registered.__name__ == "cb"
        assert events == [1]

    @pytest.mark.parametrize(
        "module",
        [
            "yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks",
            "yosai_intel_dashboard.src.infrastructure.di.service_container",
            "yosai_intel_dashboard.src.services.analytics.analytics_service",
            "yosai_intel_dashboard.src.services.upload_processing",
        ],
    )
    def test_import_all_major_components(self, module: str) -> None:
        """Importing critical modules should not raise ``ImportError``."""
        importlib.import_module(module)

    def test_service_initialization_from_di_container(self) -> None:
        """DI container should create and return registered services."""
        container = ServiceContainer()

        class Foo:
            pass

        container.register_singleton("foo", Foo)
        instance = container.get("foo")
        assert isinstance(instance, Foo)


class TestRuntimePatchesNotNeeded:
    """Ensure runtime patch scripts are obsolete."""

    def test_patch_files_absent(self) -> None:
        assert list(Path("tools").glob("step2_*")) == []
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("tools.apply_callback_patch")

    def test_callback_methods_execute_without_patch(self) -> None:
        manager = TrulyUnifiedCallbacks()
        executed: list[str] = []

        def cb() -> None:
            executed.append("ok")

        manager.register_event(CallbackEvent.BEFORE_REQUEST, cb)
        manager.trigger_event(CallbackEvent.BEFORE_REQUEST)
        assert executed == ["ok"]

    def test_upload_processor_methods_available(self) -> None:
        validator = SecurityValidator()
        class StubProcessor:
            pass
        processor = StubProcessor()
        event_bus = EventBus()
        callbacks = TrulyUnifiedCallbacks(
            event_bus=event_bus, security_validator=validator
        )
        processor_service = UploadAnalyticsProcessor(
            validator, processor, callbacks, dynamic_config.analytics, event_bus
        )
        df = pd.DataFrame({"Person ID": ["u1"], "Device name": ["d1"]})
        cleaned = processor_service.clean_uploaded_dataframe(df)
        summary = processor_service.summarize_dataframe(cleaned)
        assert summary["rows"] == 1


def main() -> int:  # pragma: no cover - convenience entry point
    import pytest
    import sys

    return pytest.main([__file__])


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
