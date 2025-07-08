import os
import sys
import importlib.util
from pathlib import Path
from typing import Any, Dict, List, Callable, Protocol, runtime_checkable, assert_type

import pandas as pd
import pytest

from core.service_container import ServiceContainer
from core.protocols import (
    AnalyticsServiceProtocol,
    ConfigurationProtocol,
    SecurityServiceProtocol,
    DatabaseProtocol,
    EventBusProtocol,
    StorageProtocol,
)
from typing import Protocol, runtime_checkable


@runtime_checkable
class DataProcessorProtocol(Protocol):
    def process_access_events(self, events: pd.DataFrame) -> pd.DataFrame: ...

    def clean_data(
        self, data: pd.DataFrame, rules: Dict[str, Any] | None = None
    ) -> pd.DataFrame: ...

    def aggregate_data(
        self, data: pd.DataFrame, groupby: List[str], metrics: List[str]
    ) -> pd.DataFrame: ...

    def validate_data_quality(self, data: pd.DataFrame) -> Dict[str, Any]: ...

    def enrich_data(self, data: pd.DataFrame, enrichment_sources: List[str]) -> pd.DataFrame: ...


@runtime_checkable
class ConfigurationProtocolStub(Protocol):
    def get_database_config(self) -> Dict[str, Any]: ...
    def get_app_config(self) -> Dict[str, Any]: ...
    def get_security_config(self) -> Dict[str, Any]: ...
    def get_upload_config(self) -> Dict[str, Any]: ...
    def reload_config(self) -> None: ...
    def validate_config(self) -> Dict[str, Any]: ...


class DummyConfig(ConfigurationProtocolStub):
    def get_database_config(self) -> Dict[str, Any]:
        return {}

    def get_app_config(self) -> Dict[str, Any]:
        return {}

    def get_security_config(self) -> Dict[str, Any]:
        return {}

    def get_upload_config(self) -> Dict[str, Any]:
        return {}

    def reload_config(self) -> None:
        pass

    def validate_config(self) -> Dict[str, Any]:
        return {"valid": True}


class DummyDatabase(DatabaseProtocol):
    def execute_query(self, query: str, params: tuple | None = None) -> pd.DataFrame:
        return pd.DataFrame()

    def execute_command(self, command: str, params: tuple | None = None) -> None:
        pass

    def begin_transaction(self) -> Any:
        return object()

    def commit_transaction(self, transaction: Any) -> None:
        pass

    def rollback_transaction(self, transaction: Any) -> None:
        pass

    def health_check(self) -> bool:
        return True

    def get_connection_info(self) -> Dict[str, Any]:
        return {}


class DummyProcessor(DataProcessorProtocol):
    def process_access_events(self, events: pd.DataFrame) -> pd.DataFrame:
        return events

    def clean_data(
        self, data: pd.DataFrame, rules: Dict[str, Any] | None = None
    ) -> pd.DataFrame:
        return data

    def aggregate_data(
        self, data: pd.DataFrame, groupby: List[str], metrics: List[str]
    ) -> pd.DataFrame:
        return data

    def validate_data_quality(self, data: pd.DataFrame) -> Dict[str, Any]:
        return {}

    def enrich_data(self, data: pd.DataFrame, enrichment_sources: List[str]) -> pd.DataFrame:
        return data


class DummyEventBus(EventBusProtocol):
    def publish(self, event_type: str, data: Dict[str, Any], source: str | None = None) -> None:
        pass

    def subscribe(self, event_type: str, handler: Callable, priority: int = 0) -> str:
        return "id"

    def unsubscribe(self, subscription_id: str) -> None:
        pass

    def get_subscribers(self, event_type: str | None = None) -> List[Dict[str, Any]]:
        return []

    def get_event_history(
        self, event_type: str | None = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        return []


class DummyStorage(StorageProtocol):
    def store_data(self, key: str, data: Any) -> str:
        return key

    def retrieve_data(self, key: str) -> Any:
        return None

    def delete_data(self, key: str) -> bool:
        return True

    def list_keys(self, prefix: str = "") -> List[str]:
        return []

    def exists(self, key: str) -> bool:
        return False

    def get_storage_info(self) -> Dict[str, Any]:
        return {}


@pytest.fixture(autouse=True)
def env_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in [
        "SECRET_KEY",
        "DB_PASSWORD",
        "AUTH0_CLIENT_ID",
        "AUTH0_CLIENT_SECRET",
        "AUTH0_DOMAIN",
        "AUTH0_AUDIENCE",
    ]:
        monkeypatch.setenv(var, "test")


def _load_real_registration_module():
    path = Path(__file__).resolve().parents[1] / "config" / "complete_service_registration.py"
    spec = importlib.util.spec_from_file_location("csr_real", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestProtocolCompliance:
    def test_configuration_service_compliance(self):
        from config.config import ConfigManager

        cfg = ConfigManager()
        assert isinstance(cfg, ConfigurationProtocol)
        assert_type(cfg, ConfigurationProtocol)

    def test_analytics_service_compliance(self):
        from services.analytics_service import AnalyticsService

        service = AnalyticsService(
            database=DummyDatabase(),
            data_processor=DummyProcessor(),
            config=DummyConfig(),
            event_bus=DummyEventBus(),
            storage=DummyStorage(),
        )
        assert isinstance(service, AnalyticsServiceProtocol)
        assert_type(service, AnalyticsServiceProtocol)

    def test_security_service_compliance(self):
        from core.security_validator import SecurityValidator

        service = SecurityValidator()
        assert isinstance(service, SecurityServiceProtocol)
        assert_type(service, SecurityServiceProtocol)

    def test_all_registered_services_implement_protocols(self):
        csr = _load_real_registration_module()
        container = ServiceContainer()
        csr.register_all_services(container)
        results = container.validate_registrations()
        assert len(results["protocol_violations"]) == 0
        assert len(results["missing_dependencies"]) == 0
