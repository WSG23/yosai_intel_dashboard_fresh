# API Service

## Endpoints

### `POST /v1/echo`

Echo the provided message.

**Request**

```json
{ "message": "hello" }
```

**Response**

```json
{ "message": "hello" }
```

## Testing

Install development dependencies and run the test suite:

```bash
pip install -r ../../requirements-dev.txt
pytest
```

To generate a coverage report:

```bash
pytest --cov --cov-report=term-missing
```
