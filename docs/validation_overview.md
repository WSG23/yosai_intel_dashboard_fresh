# Validation Overview

All validation in the Yōsai Intel Dashboard is provided by the `security` package which exposes `SecurityValidator` and `UnifiedFileValidator`. Previous individual validator classes have been removed and their functionality consolidated.

If your code imports `InputValidator` or `UploadValidator`, switch to `validation.security_validator.SecurityValidator` instead.

## Current Validation Architecture

Use the unified package for all validation needs:

Validation errors are raised using `ValidationError(field, message, code)` where
`field` identifies the offending input, `message` provides a human readable
explanation and `code` is a stable error identifier.

```python
from security import SecurityValidator, UnifiedFileValidator


validator = SecurityValidator()
file_validator = UnifiedFileValidator()

# Each validation error is raised with the field name, a message and an
# error code. This allows callers to precisely identify what went wrong.

# Input validation
result = validator.validate_input(user_input, "field_name")
if not result['valid']:
    raise ValidationError("field_name", "; ".join(result['issues']), "invalid_input")

# File upload validation (replaces SecureFileValidator)
result = file_validator.validate_file_upload(filename, file_bytes)
if not result['valid']:
    raise ValidationError("filename", "; ".join(result['issues']), "invalid_file")
```

## Validation Features

SecurityValidator provides comprehensive validation including:
- **SQL injection prevention** - Detects and blocks SQL injection attempts
- **XSS attack prevention** - Sanitizes cross-site scripting attempts  
- **Path traversal prevention** - Blocks directory traversal attacks
- **Unicode security** - Handles surrogate characters and encoding issues
- **File validation** - Checks file types, sizes, and malicious content
- **Input sanitization** - Cleans and normalizes user input

## Migration from Deprecated Classes

All legacy validators have been removed. Update your code to use
`SecurityValidator` for both input and file checks:

```python
from security import SecurityValidator, UnifiedFileValidator


validator = SecurityValidator()
file_validator = UnifiedFileValidator()
csv_bytes = df.to_csv(index=False).encode("utf-8")
result = file_validator.validate_file_upload("data.csv", csv_bytes)
result = validator.validate_input(user_input, "query_parameter")
```

## Removed Classes

These classes have been COMPLETELY REMOVED:
- ❌ `XSSPrevention`
- ❌ `SecureFileValidator`
- ❌ `BusinessLogicValidator`
- ❌ `InputValidator`
- ❌ `UploadValidator`

Use `SecurityValidator` for all validation needs.

## Testing Validation Rules

The validators can be exercised in isolation to confirm behaviour:

```python
from security import SecurityValidator

def test_rules():
    v = SecurityValidator()
    res = v.validate_input("test", "field")
    assert res["valid"]
```

## Environment Limits

When overriding configuration with environment variables, memory related values
are clamped to a maximum of **500 MB**. The following variables are affected:

- `MEMORY_THRESHOLD_MB`
- `ANALYTICS_MAX_MEMORY_MB`

If a higher value is provided, a warning will be logged and the value will be
reduced to 500 MB.

## Maintenance Notes

As of the current release there are no outstanding TODO comments related to
security validation. The `SecurityValidator` and associated utilities are
fully implemented and ready for production use.

