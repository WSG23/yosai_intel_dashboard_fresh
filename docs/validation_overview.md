# Validation Overview

All validation in the Yōsai Intel Dashboard is provided by the `validation` package which exposes both `SecurityValidator` and `FileValidator`. Previous individual validator classes have been removed and their functionality consolidated.

If your code imports `InputValidator`, `UploadValidator` or `UnifiedFileValidator`, switch to `validation.FileValidator` and `validation.SecurityValidator` instead.

## Current Validation Architecture

Use the unified package for all validation needs:

Validation errors are raised using `ValidationError(field, message, code)` where
`field` identifies the offending input, `message` provides a human readable
explanation and `code` is a stable error identifier.

```python
from validation import SecurityValidator, FileValidator


validator = SecurityValidator()
file_validator = FileValidator()

# Each validation error is raised with the field name, a message and an
# error code. This allows callers to precisely identify what went wrong.

# Input validation
result = validator.validate_input(user_input, "field_name")
if not result['valid']:
    raise ValidationError("field_name", "; ".join(result['issues']), "invalid_input")

# File upload validation
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

## Anomaly Detection

`SecurityValidator` can optionally incorporate an anomaly detection model to
score inputs. Any model with a ``predict`` method returning ``1`` for normal
values and ``-1`` for outliers can be supplied, such as scikit-learn's
``IsolationForest``:

```python
from sklearn.ensemble import IsolationForest
from validation import SecurityValidator

model = IsolationForest().fit([[len(s)] for s in ["ok", "normal"]])
validator = SecurityValidator(anomaly_model=model)

# Raises ValidationError if the model predicts an outlier
validator.validate_input("suspicious")
```

## Migration from Deprecated Classes

All legacy validators have been removed. Update your code to use
`SecurityValidator` for input checks and `FileValidator` for file uploads:

```python
from validation import SecurityValidator, FileValidator


validator = SecurityValidator()
file_validator = FileValidator()
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

Use `SecurityValidator` and `FileValidator` for all validation needs.

## Testing Validation Rules

The validators can be exercised in isolation to confirm behaviour:

```python
from validation import SecurityValidator, FileValidator

def test_rules():
    sv = SecurityValidator()
    fv = FileValidator()
    res = sv.validate_input("test", "field")
    assert res["valid"]
    assert fv.validate_file_upload("demo.csv", b"col\n1")["valid"]
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

