# Validation Overview

All validation in the Yōsai Intel Dashboard is handled by the unified `SecurityValidator` class. Previous individual validator classes have been completely removed and their functionality consolidated.

## Current Validation Architecture

Use `SecurityValidator` for all validation needs:

```python
from core.security_validator import SecurityValidator

validator = SecurityValidator()

# Input validation (replaces InputValidator, SQLInjectionPrevention, XSSPrevention)
result = validator.validate_input(user_input, "field_name")
if not result['valid']:
    raise ValidationError(result['issues'])

# File upload validation (replaces SecureFileValidator, DataFrameSecurityValidator)
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

All deprecated validator classes have been REMOVED. Update your code:

```python
# OLD (REMOVED):
from security.dataframe_validator import DataFrameSecurityValidator
validator = DataFrameSecurityValidator()
result = validator.validate_for_upload(df)

# NEW (CURRENT):
from core.security_validator import SecurityValidator
validator = SecurityValidator()
csv_bytes = df.to_csv(index=False).encode('utf-8')
result = validator.validate_file_upload("data.csv", csv_bytes)

# OLD (REMOVED):
from security.sql_validator import SQLInjectionPrevention  
SQLInjectionPrevention.validate_query_parameter(user_input)

# NEW (CURRENT):
from core.security_validator import SecurityValidator
validator = SecurityValidator()
result = validator.validate_input(user_input, "query_parameter")
```

## Removed Classes

These classes have been COMPLETELY REMOVED:
- ❌ `InputValidator` 
- ❌ `DataFrameSecurityValidator`
- ❌ `SQLInjectionPrevention`
- ❌ `XSSPrevention`
- ❌ `SecureFileValidator` 
- ❌ `BusinessLogicValidator`

Use `SecurityValidator` for all validation needs.
