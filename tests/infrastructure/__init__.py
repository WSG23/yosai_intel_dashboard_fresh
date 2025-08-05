from __future__ import annotations

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


class TestInfrastructure:
    """Context manager that prepares a lightweight test environment.

    On enter all stub packages located under ``tests/stubs`` are made
    importable and registered in :data:`sys.modules` so they override any real
    dependency.  Environment variables enabling lightweight service behaviour
    are also set.  All changes are reverted on exit.
    """

    def __init__(
        self,
        factory: MockFactory,
        *,
        stub_packages: Iterable[str] | None = None,
    ) -> None:
        self.factory = factory
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

    REQUIRED_STUBS = ("pyarrow", "pandas", "numpy")

    def setup_environment(self) -> MockFactory:
        """Install stub packages and tweak runtime settings for tests.

        The method appends ``tests/stubs`` to :data:`sys.path` and ensures
        placeholder modules for heavy optional dependencies are present in
        :data:`sys.modules`.  It returns the global :class:`MockFactory` so
        additional stubs may be registered by tests when required.
        """

        self._old_sys_path = list(sys.path)
        stubs_str = str(self._stubs_path)
        if stubs_str not in sys.path:
            sys.path.append(stubs_str)

        for name in self._discover_stubs():
            try:
                module = importlib.import_module(f"tests.stubs.{name}")
            except Exception:
                module = ModuleType(name)
            self.factory.stub(name, module)

        for name in self.REQUIRED_STUBS:
            if name not in sys.modules:
                self.factory.stub(name)

        os.environ.setdefault("LIGHTWEIGHT_SERVICES", "1")
        return self.factory

    def __enter__(self) -> MockFactory:
        return self.setup_environment()

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - cleanup
        self.factory.restore()
        os.environ.pop("LIGHTWEIGHT_SERVICES", None)
        stubs_str = str(self._stubs_path)
        if stubs_str in sys.path:
            sys.path.remove(stubs_str)
        sys.path[:] = self._old_sys_path


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
