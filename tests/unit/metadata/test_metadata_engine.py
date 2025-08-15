import sys
import types
from importlib import util as import_util
from pathlib import Path
from typing import Any, Dict, List, Protocol, Tuple, runtime_checkable

import pandas as pd
from yosai_intel_dashboard.src.core.imports.resolver import safe_import


@runtime_checkable
class UploadStorageProtocol(Protocol):
    def add_file(self, filename: str, dataframe: pd.DataFrame) -> None: ...
    def get_all_data(self) -> Dict[str, pd.DataFrame]: ...
    def clear_all(self) -> None: ...
    def load_dataframe(self, filename: str) -> pd.DataFrame | None: ...
    def get_filenames(self) -> List[str]: ...
    def get_file_info(self) -> Dict[str, Dict[str, Any]]: ...
    def wait_for_pending_saves(self) -> None: ...


@runtime_checkable
class UploadDataServiceProtocol(Protocol):
    def get_uploaded_data(self) -> Dict[str, pd.DataFrame]: ...
    def get_uploaded_filenames(self) -> List[str]: ...
    def clear_uploaded_data(self) -> None: ...
    def get_file_info(self) -> Dict[str, Dict[str, Any]]: ...
    def load_dataframe(self, filename: str) -> pd.DataFrame: ...


@runtime_checkable
class AnalyticsServiceProtocol(Protocol):
    def get_dashboard_summary(self, time_range: str = "30d") -> Dict[str, Any]: ...


class _Analytics(AnalyticsServiceProtocol):
    def get_dashboard_summary(self, time_range: str = "30d") -> Dict[str, Any]:
        return {"status": "stub"}


class _Store(UploadStorageProtocol):
    def __init__(self) -> None:
        self.data: Dict[str, pd.DataFrame] = {}

    def add_file(self, filename: str, dataframe: pd.DataFrame) -> None:
        self.data[filename] = dataframe

    def get_all_data(self) -> Dict[str, pd.DataFrame]:
        return self.data

    def clear_all(self) -> None:
        self.data.clear()

    def load_dataframe(self, filename: str) -> pd.DataFrame | None:
        return self.data.get(filename)

    def get_filenames(self) -> List[str]:
        return list(self.data.keys())

    def get_file_info(self) -> Dict[str, Dict[str, Any]]:
        return {
            k: {"rows": len(v), "columns": len(v.columns)} for k, v in self.data.items()
        }

    def wait_for_pending_saves(self) -> None:  # pragma: no cover - sync
        pass


class _DataService(UploadDataServiceProtocol):
    def __init__(self, store: _Store) -> None:
        self.store = store

    def get_uploaded_data(self) -> Dict[str, pd.DataFrame]:
        return self.store.get_all_data()

    def get_uploaded_filenames(self) -> List[str]:
        return self.store.get_filenames()

    def clear_uploaded_data(self) -> None:
        self.store.clear_all()

    def get_file_info(self) -> Dict[str, Dict[str, Any]]:
        return self.store.get_file_info()

    def load_dataframe(self, filename: str) -> pd.DataFrame:
        df = self.store.load_dataframe(filename)
        if df is None:
            raise FileNotFoundError(filename)
        return df


def _create_engine() -> Tuple[Any, _Store]:
    store = _Store()
    analytics = _Analytics()
    mod_path = (
        Path(__file__).resolve().parents[2]
        / "services"
        / "metadata_enhancement_engine.py"
    )
    spec = import_util.spec_from_file_location("metadata", mod_path)
    metadata = import_util.module_from_spec(spec)
    assert spec.loader is not None
    services_stub = types.ModuleType("services")
    upload_mod = types.ModuleType("services.upload")
    upload_proto_mod = types.ModuleType("services.upload.protocols")
    upload_proto_mod.UploadDataServiceProtocol = UploadDataServiceProtocol
    analytics_mod = types.ModuleType("services.analytics")
    analytics_proto_mod = types.ModuleType("services.analytics.protocols")
    analytics_proto_mod.AnalyticsServiceProtocol = AnalyticsServiceProtocol
    services_stub.upload = upload_mod
    services_stub.analytics = analytics_mod
    safe_import('services', services_stub)
    safe_import('services.upload', upload_mod)
    safe_import('services.upload.protocols', upload_proto_mod)
    safe_import('services.analytics', analytics_mod)
    safe_import('services.analytics.protocols', analytics_proto_mod)
    import tests.stubs.dash as dash_stub

    safe_import('dash', dash_stub)
    safe_import('dash.html', dash_stub.html)
    safe_import('dash.dcc', dash_stub.dcc)
    safe_import('dash.dependencies', dash_stub.dependencies)
    safe_import('dash._callback', dash_stub._callback)
    dash_stub.no_update = dash_stub._callback.NoUpdate()
    sys.modules.setdefault(
        "dash.exceptions", types.SimpleNamespace(PreventUpdate=Exception)
    )
    sys.modules.setdefault(
        "flask_caching",
        import_util.module_from_spec(
            import_util.spec_from_loader("flask_caching", loader=None)
        ),
    )
    sys.modules["flask_caching"].Cache = type("Cache", (), {})
    sys.modules.setdefault(spec.name, metadata)
    spec.loader.exec_module(metadata)
    engine = metadata.MetadataEnhancementEngine(
        upload_data_service=_DataService(store),
        analytics_service=analytics,
    )
    return engine, store


def test_enhance_metadata_basic() -> None:
    engine, store = _create_engine()
    df = pd.DataFrame(
        {
            "timestamp": ["2024-01-01 00:00:00", "2024-01-01 01:00:00"],
            "person_id": ["u1", "u2"],
            "door_id": ["d1", "d1"],
            "access_result": ["Granted", "Denied"],
        }
    )
    store.add_file("sample.csv", df)

    result = engine.enhance_metadata()

    assert result["behavior"]["unique_users"] == 2
    assert result["security"]["denied_rate"] == 0.5
    assert result["compliance"]["compliant"] is True
    assert result["analytics"]["status"] == "stub"


def test_compliance_failure() -> None:
    engine, store = _create_engine()
    df = pd.DataFrame({"person_id": ["u1"]})
    store.add_file("broken.csv", df)

    result = engine.enhance_metadata()

    assert result["compliance"]["compliant"] is False
    assert "door_id" in result["compliance"]["missing_columns"]
