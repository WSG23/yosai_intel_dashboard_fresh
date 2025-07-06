# Validation Overview

This dashboard previously exposed multiple independent validators. These have
now been consolidated into the unified `SecurityValidator` which handles string,
file and DataFrame checks in one place. Use the examples below to migrate any
existing validation code.

## SecurityValidator

- **Purpose**: Perform all input, file and DataFrame validation with consistent
  security rules.
- **Use when**: Sanitizing any external data before database writes or analysis.


```python
from core.security_validator import SecurityValidator

validator = SecurityValidator()
validator.validate_input(user_name, "user_name")
validator.validate_file_upload(filename, file_bytes)
```

The `SecurityValidator` and `UnifiedFileValidator` replace the old
`InputValidator`, `SecureFileValidator`, `DataFrameSecurityValidator`,
`SQLInjectionPrevention`, `XSSPrevention`, `BusinessLogicValidator` and
`SecretsValidator` classes.
All of these wrappers now delegate to the unified validator and will be removed
in a future release.

### Migration Steps

1. Replace imports of the legacy validator classes with
   `SecurityValidator` from `core.security_validator`.
2. Update code that called `validate()` or `validate_file_upload()` on the old
   classes to use the corresponding `SecurityValidator` methods.
3. If your module relied on the generic `Validator` protocol, it remains
   compatible with the new class.

## Best Practices
- Validate data as early as possible using `SecurityValidator`.
- Run `validate_file_upload()` on files before saving or parsing.
- Use `DataFrameSecurityValidator` when processing large data sets.
- Sanitize all query parameters with `validate_input()`.
- Rotate secrets regularly and validate them during startup.

## Example Scenarios
- **User search input**: `SecurityValidator.validate_input()` before constructing a query.
- **CSV upload**: `SecurityValidator.validate_file_upload()` then `DataFrameSecurityValidator.validate_for_analysis()`.
- **Displaying comments**: `SecurityValidator.validate_input()` when accepting the comment.


Example usage of the processor:
```python
from core.unicode import get_text_processor
processor = get_text_processor()
cleaned = processor.safe_encode_text(user_input)
```

## ClientSideValidator

Uploads are checked in the browser before being sent to the server.  The
`ClientSideValidator` mirrors these rules on the server so behaviour is
consistent regardless of where validation occurs.

Key rules enforced:

- **Magic number checks** – file headers must match their extension.
- **Size limits** – configurable per file type with a global fallback.
- **Duplicate detection** – repeated filenames are rejected in a single batch.
- **Custom hooks** – optional callbacks allow bespoke validation logic.

The validator exposes a JSON configuration via `to_json()` used by the
`upload-handlers.js` script to apply the same checks client-side.
