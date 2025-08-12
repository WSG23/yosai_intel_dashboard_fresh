# API Service

This FastAPI application provides simple health and echo endpoints for testing and development.

## Available Endpoints

### `GET /health`
Returns a JSON object indicating service status.

```bash
curl http://localhost:8000/health
```

### `POST /echo`
Echoes back the request payload as raw bytes.

```bash
curl -X POST http://localhost:8000/echo -d 'hello world'
```

## Authentication

These endpoints do not require authentication.

## API Documentation

Interactive Swagger docs are available at `http://localhost:8000/docs` and Redoc at `http://localhost:8000/redoc`.
The OpenAPI specification can be accessed at `http://localhost:8000/openapi.json`.

## Running Locally

Install dependencies and start the server:

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Alternatively, from the repository root you can run the unified startup script:

```bash
python start_api.py
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
