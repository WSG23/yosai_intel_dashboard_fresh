# Service Builder Migration Guide

This guide explains how to transition existing services from the
legacy `BaseService` class to the new builder pattern and how to adopt
the unified validation package.

## Switching from `BaseService`

Old approach:
```python
from yosai_framework.service import BaseService

service = BaseService("analytics", "config/service.yaml")
service.start()
```

New approach using the builder:
```python
from yosai_framework.builder import ServiceBuilder

service = (
    ServiceBuilder("analytics")
    .with_config("config/service.yaml")
    .with_logging()
    .with_metrics("0.0.0.0:9102")
    .with_health()
    .build()
)
service.start()
```

`ServiceBuilder` allows features such as logging, metrics and health
checks to be toggled as needed before constructing the final service
instance.

## Replacing Direct Validator Usage

Import validators from the `validation` package rather than accessing the
modules directly:

```python
from sklearn.ensemble import IsolationForest
from validation import SecurityValidator, FileValidator

model = IsolationForest().fit([[1], [2], [3]])
validator = SecurityValidator(anomaly_model=model)
file_validator = FileValidator()
```

The package consolidates all validation utilities and keeps the
interface stable while internal implementations evolve.

## Isolated Component Testing Examples

### Logging
```python
from yosai_framework.builder import ServiceBuilder

def test_logging():
    svc = ServiceBuilder("demo").with_logging(level="DEBUG").build()
    svc.log.debug("ready")
```

### Metrics
```python
from yosai_framework.builder import ServiceBuilder

def test_metrics(tmp_path):
    svc = ServiceBuilder("demo").with_metrics("127.0.0.1:9000").build()
    assert svc.registry is not None
```

### Health Endpoints
```python
from yosai_framework.builder import ServiceBuilder
from fastapi.testclient import TestClient

def test_health():
    svc = ServiceBuilder("demo").with_health().build()
    client = TestClient(svc.app)
    assert client.get("/health").json() == {"status": "ok"}
```

### Validation Rules
```python
from sklearn.ensemble import IsolationForest
from validation import SecurityValidator, FileValidator

def test_validation():
    model = IsolationForest().fit([[1], [2], [3]])
    sv = SecurityValidator(anomaly_model=model)
    fv = FileValidator()
    result = sv.validate_input("SELECT 1", "query")
    assert result["valid"]
    assert fv.validate_file_upload("demo.csv", b"col\n1")["valid"]
```
