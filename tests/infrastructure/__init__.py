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

import atexit
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
    # Helper creators
    # ------------------------------------------------------------------
    @staticmethod
    def dataframe(data: Dict[str, Iterable] | None = None):
        """Return a lightweight :class:`pandas.DataFrame` built from ``data``."""

        import pandas as pd  # imported lazily so stubs apply

        return pd.DataFrame(data or {})

    @staticmethod
    def upload_processor():
        """Return a lightweight processor analysing uploaded data."""

        from tests.stubs.utils.upload_store import get_uploaded_data_store

        def _shape(df):
            if hasattr(df, "shape"):
                return df.shape
            data = getattr(df, "args", [{}])[0]
            rows = len(next(iter(data.values()))) if data else 0
            cols = len(data)
            return rows, cols

        class _Processor:
            def analyze_uploaded_data(self):
                store = get_uploaded_data_store()
                data = {
                    name: df
                    for name, df in store.get_all_data().items()
                    if _shape(df)[0]
                }
                if not data:
                    return {"status": "no_data"}
                rows, cols = _shape(list(data.values())[0])
                return {"status": "success", "rows": rows, "columns": cols}

        return _Processor()


class TestInfrastructure:
    """Context manager that prepares a lightweight test environment.

    On enter all stub packages located under ``tests/stubs`` are made importable
    and registered in :data:`sys.modules` so they override any real dependency.
    Environment variables enabling lightweight service behaviour are also set.
    All changes are reverted on exit.
    """

    def __init__(
        self,
        factory: MockFactory | None = None,
        *,
        stub_packages: Iterable[str] | None = None,
    ) -> None:
        self.factory = factory or MockFactory()
        self.stub_packages = list(stub_packages or [])
        self._stubs_path = Path(__file__).resolve().parents[1] / "stubs"
        self._old_sys_path: list[str] = []

    def _discover_stubs(self) -> Iterable[str]:
        if self.stub_packages:
            return self.stub_packages
        if not self._stubs_path.exists():
            return []
        names = []
        for entry in self._stubs_path.iterdir():
            if entry.name == "__pycache__":
                continue
            if entry.is_dir() or entry.suffix == ".py":
                names.append(entry.stem)
        return names


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
    # Convenience helpers
    # ------------------------------------------------------------------
    def setup_environment(self) -> MockFactory:
        """Enter the context immediately and register cleanup at exit."""

        factory = self.__enter__()
        atexit.register(self.__exit__, None, None, None)
        return factory


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
