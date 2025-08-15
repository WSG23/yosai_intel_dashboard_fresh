"""Utilities to set up a lightweight testing environment.

The module provides helpers for installing stub modules and configuring
environment variables required by tests.  It also exposes
``uploaded_data`` which builds a mapping of filenames to ``pandas``
DataFrames for upload-related tests.

"""

from __future__ import annotations

import atexit
import importlib
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Iterable, Iterator, Mapping

import pandas as pd

import pytest



class MockFactory:
    """Factory responsible for installing and removing stub modules."""

        import pandas as pd

    def stub(self, name: str, module: ModuleType | None = None) -> ModuleType:
        """Register ``module`` under ``name`` in :data:`sys.modules`."""


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
        self.factory = factory or mock_factory

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

        The method appends ``tests/unit/stubs`` to :data:`sys.path` and ensures
        placeholder modules for heavy optional dependencies are present in
        :data:`sys.modules`.  It returns the global :class:`MockFactory` so
        additional stubs may be registered by tests when required.
        """

        self._old_sys_path = list(sys.path)
        stubs_str = str(self._stubs_path)
        if stubs_str not in sys.path:
            sys.path.append(stubs_str)

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

    # ------------------------------------------------------------------
    def setup_environment(self) -> MockFactory:
        """Set up the environment immediately and return the factory."""

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

    def setup_environment(self) -> None:
        """Activate the test environment without using a context manager."""
        self.__enter__()



def uploaded_data(*dfs: tuple[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Return a dictionary mapping filenames to DataFrames."""

    return {name: df for name, df in dfs}


mock_factory = MockFactory()


@pytest.fixture(scope="session")
def test_env() -> TestInfrastructure:
    infra = TestInfrastructure()
    infra.setup_environment()
    return infra


@contextmanager
def setup_test_environment() -> Iterator[MockFactory]:
    """Prepare a lightweight environment for tests.


# ----------------------------------------------------------------------
def uploaded_data(valid_df):
    """Return a typical uploaded data mapping used in tests."""

    import pandas as pd

    return {"empty.csv": pd.DataFrame(), "valid.csv": valid_df}


__all__ = [
    "MockFactory",
    "TestInfrastructure",
    "setup_test_environment",
    "uploaded_data",
    "mock_factory",
    "test_env",
]
