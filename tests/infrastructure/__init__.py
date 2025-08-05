"""Utilities for constructing common objects used in tests.

This module provides two small helpers:

``TestInfrastructure``
    Prepares a minimal environment so tests can run without optional
    dependencies.  It adds ``tests/stubs`` to ``sys.path`` and ensures that
    light‑weight stand‑ins for heavy packages such as :mod:`pyarrow`,
    :mod:`pandas` and :mod:`numpy` are present in :data:`sys.modules`.

``MockFactory``
    Convenience factory that wires together frequently used objects like
    :class:`SecurityValidator` or :class:`UploadAnalyticsProcessor`.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Dict


class TestInfrastructure:
    """Prepare the Python environment for tests."""

    def __init__(self) -> None:
        self._stubs_path = Path(__file__).resolve().parents[1] / "stubs"

    # ------------------------------------------------------------------
    def setup_environment(self) -> None:
        """Register stub modules and make ``tests/stubs`` importable."""

        stubs = str(self._stubs_path)
        if stubs not in sys.path:
            sys.path.insert(0, stubs)

        for name in ("pyarrow", "pandas", "numpy"):
            if name in sys.modules:
                continue
            try:
                importlib.import_module(name)
            except Exception:  # pragma: no cover - best effort
                try:
                    sys.modules[name] = importlib.import_module(f"tests.stubs.{name}")
                except Exception:  # pragma: no cover - defensive
                    sys.modules[name] = ModuleType(name)


class MockFactory:
    """Factory that exposes common building blocks for tests."""

    # ------------------------------------------------------------------
    def security_validator(self):
        from validation.security_validator import SecurityValidator

        return SecurityValidator()

    # ------------------------------------------------------------------
    def processor(self, validator=None):
        from yosai_intel_dashboard.src.services.data_processing.processor import (
            Processor,
        )

        validator = validator or self.security_validator()
        return Processor(validator=validator)

    # ------------------------------------------------------------------
    def callback_manager(self, event_bus=None, validator=None):
        from yosai_intel_dashboard.src.core.events import EventBus
        from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import (
            TrulyUnifiedCallbacks,
        )

        event_bus = event_bus or EventBus()
        validator = validator or self.security_validator()
        return TrulyUnifiedCallbacks(event_bus=event_bus, security_validator=validator)

    # ------------------------------------------------------------------
    def upload_processor(self):
        from yosai_intel_dashboard.src.core.events import EventBus
        from yosai_intel_dashboard.src.infrastructure.config.dynamic_config import (
            dynamic_config,
        )
        from yosai_intel_dashboard.src.services.analytics.upload_analytics import (
            UploadAnalyticsProcessor,
        )

        validator = self.security_validator()
        processor = self.processor(validator)
        event_bus = EventBus()
        callbacks = self.callback_manager(event_bus, validator)
        return UploadAnalyticsProcessor(
            validator, processor, callbacks, dynamic_config.analytics, event_bus
        )

    # ------------------------------------------------------------------
    def dataframe(self, columns: Dict[str, Any]):
        from tests.utils.builders import DataFrameBuilder

        builder = DataFrameBuilder()
        for name, values in columns.items():
            builder.add_column(name, values)
        return builder.build()


# ----------------------------------------------------------------------
def uploaded_data(valid_df):
    """Return a typical uploaded data mapping used in tests."""

    import pandas as pd

    return {"empty.csv": pd.DataFrame(), "valid.csv": valid_df}


__all__ = ["TestInfrastructure", "MockFactory", "uploaded_data"]
