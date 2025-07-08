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
from core.service_container import ServiceContainer
from services.interfaces import UploadValidatorProtocol

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

Several tests provide custom stubs that implement these protocols. They avoid heavy dependencies like Dash or database connections. See `tests/test_service_integration.py` and `tests/test_protocol_compliance.py` for examples of simple stubs providing the minimum required behaviour.

Use this approach to isolate units under test and speed up execution.
