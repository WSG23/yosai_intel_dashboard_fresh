from __future__ import annotations

import importlib
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Iterable, Iterator, Mapping


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
    # Helpers for common test objects
    # ------------------------------------------------------------------
    def dataframe(self, data: Mapping[str, Iterable[Any]] | None = None):
        """Return a ``pandas`` DataFrame built from ``data``."""

        import pandas as pd

        return pd.DataFrame(data or {})

    def upload_processor(self):
        """Create a configured :class:`UploadAnalyticsProcessor` instance."""

        import pandas as pd

        class DummyUploadProcessor:
            """Lightweight stand-in for :class:`UploadAnalyticsProcessor`."""

            def load_uploaded_data(self):
                return {}

            def _load_data(self):
                return self.load_uploaded_data()

            def clean_uploaded_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
                if df.empty:
                    return df.copy()
                cleaned = df.dropna(how="all", axis=0).dropna(how="all", axis=1).copy()
                cleaned.columns = [c.strip().lower().replace(" ", "_") for c in cleaned.columns]
                cleaned = cleaned.rename(columns={"device_name": "door_id", "event_time": "timestamp"})
                if "timestamp" in cleaned.columns:
                    cleaned["timestamp"] = pd.to_datetime(cleaned["timestamp"], errors="coerce")
                cleaned = cleaned.dropna(how="all", axis=0)
                return cleaned

            def _validate_data(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
                cleaned: Dict[str, pd.DataFrame] = {}
                for name, df in data.items():
                    dfc = self.clean_uploaded_dataframe(df)
                    if not dfc.empty:
                        cleaned[name] = dfc
                return cleaned

            def _calculate_statistics(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
                if not data:
                    return {
                        "rows": 0,
                        "columns": 0,
                        "column_names": [],
                        "dtypes": {},
                        "memory_usage": 0,
                        "null_counts": {},
                        "total_events": 0,
                        "active_users": 0,
                        "active_doors": 0,
                        "date_range": {"start": "Unknown", "end": "Unknown"},
                    }

                combined = pd.concat(list(data.values()), ignore_index=True)
                summary = {
                    "rows": int(combined.shape[0]),
                    "columns": int(combined.shape[1]),
                    "dtypes": {col: str(dtype) for col, dtype in combined.dtypes.items()},
                    "memory_usage": int(combined.memory_usage(deep=True).sum()),
                    "null_counts": {col: int(combined[col].isna().sum()) for col in combined.columns},
                }
                active_users = combined["person_id"].nunique() if "person_id" in combined.columns else 0
                active_doors = combined["door_id"].nunique() if "door_id" in combined.columns else 0
                date_range = {"start": "Unknown", "end": "Unknown"}
                if "timestamp" in combined.columns:
                    ts = pd.to_datetime(combined["timestamp"], errors="coerce").dropna()
                    if not ts.empty:
                        date_range = {"start": str(ts.min().date()), "end": str(ts.max().date())}
                summary.update(
                    {
                        "column_names": list(combined.columns),
                        "total_events": int(combined.shape[0]),
                        "active_users": int(active_users),
                        "active_doors": int(active_doors),
                        "date_range": date_range,
                    }
                )
                return summary

            def _format_results(self, stats: Dict[str, Any]) -> Dict[str, Any]:
                result = dict(stats)
                result["status"] = result.get("status", "success")
                return result

            def _process_uploaded_data_directly(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
                return self._calculate_statistics(self._validate_data(data))

        return DummyUploadProcessor()


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
