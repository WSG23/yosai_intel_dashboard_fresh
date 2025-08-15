# Testing Architecture

This project uses **protocols** and a simple dependency injection container to keep services loosely coupled and easy to test. New service interfaces live in `services/` and are defined using Python `Protocol` classes. Components depend only on these interfaces so tests can supply lightweight replacements.

## Service Protocols

The following protocols describe the core behaviour expected from each service. Implementations are registered with the `ServiceContainer` and can be swapped during tests:

- `UploadValidatorProtocol`
- `ExportServiceProtocol`
- `DoorMappingServiceProtocol`
- `SecurityServiceProtocol`
- `AuthenticationProtocol`

These interfaces can be found under `services/interfaces.py` and `services/security/protocols.py`.

## Dependency Injection

`ServiceContainer` in `core.service_container` manages service lifetimes and resolves dependencies based on the protocols. Services register themselves as singletons or transients. Test suites create a fresh container and register stubs or mocks as needed:

```python
from yosai_intel_dashboard.src.simple_di import ServiceContainer
from yosai_intel_dashboard.src.services.interfaces import UploadValidatorProtocol

class DummyValidator(UploadValidatorProtocol):
    def validate(self, filename: str, content: str) -> tuple[bool, str]:
        return True, ""

    def to_json(self) -> str:
        return "{}"

container = ServiceContainer()
container.register_singleton("upload_validator", DummyValidator)
```

Tests then retrieve `upload_validator` from the container and pass it to the component under test.

## Sample Test Doubles

Several tests provide custom stubs that implement these protocols. They avoid heavy dependencies like Dash or database connections. See `tests/unit/test_service_integration.py` and `tests/unit/test_protocol_compliance.py` for examples of simple stubs providing the minimum required behaviour.

Use this approach to isolate units under test and speed up execution.

## New Protocols

Additional protocols live in `core.protocols` and `services/upload/protocols.py`.
They cover database access, logging, event handling and Unicode processing.  The
most frequently used interfaces are:

- `DatabaseProtocol`
- `LoggingProtocol`
- `CallbackSystemProtocol`
- `UnicodeProcessorProtocol`

Each protocol can be satisfied by lightweight fakes during testing.

## Dependency Injection Patterns

`ServiceContainer` supports singletons, transients and factories. A factory
function is executed on first resolution and the instance is cached:

```python
from yosai_intel_dashboard.src.simple_di import ServiceContainer

container = ServiceContainer()
container.register_singleton("logger", DummyLogger())
container.register_factory("db", lambda c: FakeDatabase())
container.register_transient("processor", FileProcessor)
```

Registrations can be validated with `validate_registrations()` and health checks
can be attached via `register_health_check()`.

## Builder Utilities

The `tests/unit/utils` package provides helpers for assembling complex objects:

- `DataFrameBuilder` – quick creation of pandas DataFrames
- `UploadFileBuilder` – encode DataFrames as upload content
- `PluginPackageBuilder` – temporary plugin packages for integration tests

These builders keep test setup short and expressive.

## Example Container Setup

Tests typically create a fresh container with fakes registered:

```python
from yosai_intel_dashboard.src.simple_di import ServiceContainer
from tests.unit.fakes import FakeUploadStore, FakeDeviceLearningService

@pytest.fixture
def container():
    c = ServiceContainer()
    c.register_singleton("upload_storage", FakeUploadStore())
    c.register_singleton("device_learning_service", FakeDeviceLearningService())
    return c


def test_process_uploads(container):
    processor = UploadProcessingService(
        store=container.get("upload_storage"),
        learning_service=container.get("device_learning_service"),
    )
    # assert on processor behaviour
```

Run the suite with `pytest` and each test receives a clean container.

## Migrating from `sys.modules` Stubs

Older tests injected doubles by overwriting modules:

```python
import sys, types

analytics_stub = types.ModuleType("services.analytics_service")
analytics_stub.AnalyticsService = DummyAnalytics
sys.modules["services.analytics_service"] = analytics_stub
```

Using the container removes the need for module manipulation:

```python
from yosai_intel_dashboard.src.simple_di import ServiceContainer

container = ServiceContainer()
container.register_singleton("analytics_service", DummyAnalytics())
```

Pass the container to the unit under test and drop the `sys.modules` setup.

The `tools/migrate_tests.py` helper automates this refactor. Running

```bash
python tools/migrate_tests.py --apply path/to/test_file.py
```

comments out the old `sys.modules` lines and imports protocol test doubles from
`tests.stubs` so tests run against the lightweight implementations.
