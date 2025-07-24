# Validation Overview

All validation in the Yōsai Intel Dashboard is handled by the unified `SecurityValidator` class. Previous individual validator classes have been completely removed and their functionality consolidated.

## Current Validation Architecture

Use `SecurityValidator` for all validation needs:

```python
from validation.security_validator import SecurityValidator

validator = SecurityValidator()

# Input validation
result = validator.validate_input(user_input, "field_name")
if not result['valid']:
    raise ValidationError(result['issues'])

# File upload validation (replaces SecureFileValidator)
result = validator.validate_file_upload(filename, file_bytes)
if not result['valid']:
    raise ValidationError(result['issues'])
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
from validation.security_validator import SecurityValidator

validator = SecurityValidator()
csv_bytes = df.to_csv(index=False).encode("utf-8")
result = validator.validate_file_upload("data.csv", csv_bytes)
result = validator.validate_input(user_input, "query_parameter")
```

## Removed Classes

These classes have been COMPLETELY REMOVED:
- ❌ `XSSPrevention`
- ❌ `SecureFileValidator`
- ❌ `BusinessLogicValidator`

Use `SecurityValidator` for all validation needs.

## Environment Limits

When overriding configuration with environment variables, memory related values
are clamped to a maximum of **500 MB**. The following variables are affected:

- `MEMORY_THRESHOLD_MB`
- `ANALYTICS_MAX_MEMORY_MB`

If a higher value is provided, a warning will be logged and the value will be
reduced to 500 MB.

