# Upload Endpoint PR Notes

## New Endpoint
- `POST /api/v2/uploads/results` creates a new results entry for an uploaded file.
- Accepts multipart form data with the file payload and optional metadata.
- Returns the created result record once processing completes.

## Schemas
**UploadResult**
```json
{
  "id": 1,
  "filename": "report.csv",
  "status": "processed",
  "created_at": "2024-05-01T12:00:00Z"
}
```

**UploadRequest**
```json
{
  "file": "<binary>",
  "metadata": { "source": "client" }
}
```

## Migration Notes
- Adds a new `uploads` table with columns `id`, `filename`, `status`, `created_at`.
- Foreign key to `users` table associates uploads with the submitting user.
- Run the migration with `alembic upgrade head` after deploying.

## Example `results[]` Payload
```json
{
  "results": [
    { "id": 1, "status": "processed", "duration_ms": 345 },
    { "id": 2, "status": "failed", "duration_ms": 120 }
  ]
}
```

## Running Tests
```bash
# Backend tests
pytest tests/test_upload_endpoint.py -q

# Lint updated docs
pre-commit run --files docs/pr/Upload_PR.md README.md
```
