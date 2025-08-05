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
    """Factory responsible for installing and removing stub modules."""

    def __init__(self) -> None:
        self._originals: Dict[str, ModuleType | None] = {}
        self._installed: set[str] = set()

    def stub(self, name: str, module: ModuleType | None = None) -> ModuleType:
        """Register ``module`` under ``name`` in :data:`sys.modules`."""

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
    # Component helpers
    # ------------------------------------------------------------------
    def file_processor(self):
        """Return a new :class:`FileProcessor` instance."""

        from yosai_intel_dashboard.src.services.data_processing.file_processor import (
            FileProcessor,
        )

        return FileProcessor()

    def upload_processor(self):
        """Return a minimal upload analytics processor mock."""

        class _UploadProcessor:
            def load_uploaded_data(self):  # pragma: no cover - patched in tests
                return {}

            def analyze_uploaded_data(self):
                data = self.load_uploaded_data()
                if not data:
                    return {"status": "no_data"}
                df = next(iter(data.values()))
                rows = len(df)
                return {"status": "success", "rows": int(rows)}

        return _UploadProcessor()

    def dataframe(self):
        """Return a minimal DataFrame-like object."""

        class _DF:
            shape = (1, 2)

            def __len__(self) -> int:
                return 1

        return _DF()


class TestInfrastructure:
    """Prepare a lightweight test environment."""

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
    def setup_environment(self) -> MockFactory:
        """Set up the environment immediately and return the factory."""

        self.__enter__()
        atexit.register(self.__exit__, None, None, None)
        return self.factory


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
