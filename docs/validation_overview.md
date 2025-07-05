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

The `SecurityValidator` replaces the old `InputValidator`,
`SecureFileValidator`, `DataFrameSecurityValidator`, `SQLInjectionPrevention`,
`XSSPrevention`, `BusinessLogicValidator` and `SecretsValidator` classes.
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
from core.unicode_processor import UnicodeProcessor
cleaned = UnicodeProcessor.safe_encode_text(user_input)
```
