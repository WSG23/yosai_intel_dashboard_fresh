from __future__ import annotations

import atexit
import importlib
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType
from typing import Dict, Iterable, Iterator


class MockFactory:
    """Factory responsible for installing and removing stub modules.

    The factory keeps track of all modules it injects into ``sys.modules`` so
    the original modules can be restored once tests complete.
    """

    def __init__(self) -> None:
        self._originals: Dict[str, ModuleType | None] = {}
        self._installed: set[str] = set()

    def stub(self, name: str, module: ModuleType | None = None) -> ModuleType:
        """Register ``module`` under ``name`` in ``sys.modules``.

        If no module is provided a new empty :class:`ModuleType` is created.
        The previous module (if any) is stored so it can be restored later.
        """

        if name not in self._originals:
            self._originals[name] = sys.modules.get(name)
        if module is None:
            module = ModuleType(name.rsplit(".", 1)[-1])
        sys.modules[name] = module
        self._installed.add(name)
        return module

    def restore(self) -> None:
        """Restore all modules that were previously stubbed."""

        for name in list(self._installed):
            original = self._originals.get(name)
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original
        self._installed.clear()
        self._originals.clear()

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
        """Instantiate an ``UploadAnalyticsProcessor`` with default dependencies."""

        from types import SimpleNamespace

        from validation.security_validator import SecurityValidator
        from yosai_intel_dashboard.src.core.events import EventBus
        from yosai_intel_dashboard.src.infrastructure.callbacks import unified_callbacks
        from yosai_intel_dashboard.src.services.analytics.upload_analytics import (
            UploadAnalyticsProcessor,
        )
        from yosai_intel_dashboard.src.services.data_processing.processor import (
            Processor,
        )

        validator = SecurityValidator()
        processor = Processor(validator=validator)
        event_bus = EventBus()
        callbacks = unified_callbacks.TrulyUnifiedCallbacks(
            event_bus=event_bus, security_validator=validator
        )
        analytics_config = SimpleNamespace()
        return UploadAnalyticsProcessor(
            validator, processor, callbacks, analytics_config, event_bus
        )


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

    def __enter__(self) -> MockFactory:
        self._old_sys_path = list(sys.path)
        stubs_str = str(self._stubs_path)
        if stubs_str not in sys.path:
            sys.path.insert(0, stubs_str)

        for name in self._discover_stubs():
            try:
                module = importlib.import_module(f"tests.stubs.{name}")
            except Exception:
                module = ModuleType(name)
            self.factory.stub(name, module)

        os.environ.setdefault("LIGHTWEIGHT_SERVICES", "1")
        return self.factory

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - cleanup
        self.factory.restore()
        os.environ.pop("LIGHTWEIGHT_SERVICES", None)
        stubs_str = str(self._stubs_path)
        if stubs_str in sys.path:
            sys.path.remove(stubs_str)
        sys.path[:] = self._old_sys_path

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------
    def setup_environment(self) -> MockFactory:
        """Enter the context immediately and register cleanup at exit."""

        factory = self.__enter__()
        atexit.register(self.__exit__, None, None, None)
        return factory


mock_factory = MockFactory()


@contextmanager
def setup_test_environment() -> Iterator[MockFactory]:
    """Prepare a lightweight environment for tests.

    The context manager installs stub packages and yields the global
    :class:`MockFactory` so tests can register additional stubs if required.
    All changes are reverted when the context exits.
    """

    infra = TestInfrastructure(mock_factory)
    with infra:
        yield mock_factory


__all__ = [
    "MockFactory",
    "TestInfrastructure",
    "setup_test_environment",
    "mock_factory",
]
