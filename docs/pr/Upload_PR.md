# Upload Results Endpoint

This document summarizes the new `/api/v1/results/upload` endpoint, associated schema, migration notes, and test commands.

## Endpoint Summary

`POST /api/v1/results/upload`

Accepts an array of result objects via the `results[]` field and returns a 202 response once the upload is queued for processing.

### Example `results[]` Payload

```json
{
  "results": [
    {
      "result_id": 1,
      "device_id": "door-123",
      "status": "processed",
      "timestamp": "2024-07-01T12:00:00Z"
    }
  ]
}
```

## Schema

| Field       | Type    | Notes                            |
|-------------|---------|----------------------------------|
| result_id   | integer | Unique identifier for the result |
| device_id   | string  | Source device identifier         |
| status      | string  | Processing state                 |
| timestamp   | string  | ISO‑8601 formatted datetime      |

## Migration Notes

1. A new `results` table stores uploaded result records.
2. Apply the migration:

```sh
alembic upgrade head
```

## Test Commands

Run the following commands before opening a pull request to verify formatting, linting, and tests for both backend and frontend:

```sh
python -m pip install -r requirements-dev.txt
black --check .
ruff check .
pytest -q
npm install
npm test
```
