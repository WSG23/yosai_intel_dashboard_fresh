# Error Response Contract

All services return errors in a unified JSON structure:

```json
{
  "code": "invalid_input",
  "message": "human readable message",
  "details": {"optional": "context"}
}
```

The `code` field is one of the following values defined in `shared/errors`:

- `invalid_input` – the request payload failed validation
- `unauthorized` – the caller is not authorized
- `not_found` – the requested resource does not exist
- `internal` – an unexpected server error occurred
- `unavailable` – the service is temporarily unavailable

Both Python and Go components map internal exceptions to these codes and all
HTTP handlers use this structure for error responses.
