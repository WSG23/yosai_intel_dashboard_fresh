# Validation Overview

This dashboard includes several validators that sanitize input and uploaded data before any processing occurs. Use this guide to choose the right validator for each scenario.

## Validators

### InputValidator
- **Purpose**: Clean individual strings using Unicode normalization and simple XSS pattern checks.
- **Use when**: Accepting form fields, query parameters or any user supplied text.
- Internally uses `core.unicode_processor.UnicodeProcessor` for thorough text cleaning.

### SecureFileValidator
- **Purpose**: Safely decode base64 uploads, enforce filename rules and parse CSV/JSON/XLSX files.
- **Use when**: Handling file uploads from the UI or API.

### DataFrameSecurityValidator
- **Purpose**: Ensure Pandas DataFrames are safe for processing. Checks memory limits, removes dangerous formulas and supports chunked analysis.
- **Use when**: Processing uploaded datasets or database queries represented as DataFrames.

### SQLInjectionPrevention
- **Purpose**: Sanitize SQL parameters and statements and enforce parameterized queries.
- **Use when**: Building dynamic SQL or validating search terms used in database queries.

### XSSPrevention
- **Purpose**: Escape HTML fragments before rendering to the browser.
- **Use when**: Returning user provided comments or other rich text in templates.

### BusinessLogicValidator
- **Purpose**: Placeholder for domain specific checks on data structures.
- **Use when**: Custom application rules require validation beyond generic security checks.

### SecretsValidator
- **Purpose**: Audit configuration secrets for insecure patterns and entropy.
- **Use when**: Validating environment variables or application keys during startup.

## Best Practices
- Validate data as early as possible after receiving it.
- Combine validators if input passes through multiple layers (e.g., `SecureFileValidator` then `DataFrameSecurityValidator`).
- Use `SQLInjectionPrevention` for any data that is incorporated into SQL queries.
- Escape user provided output with `XSSPrevention` before rendering HTML.
- Periodically run `SecretsValidator` on stored credentials.

## Example Scenarios
- **User search input**: `InputValidator` → `SQLInjectionPrevention` before constructing a query.
- **CSV upload**: `SecureFileValidator` to parse the file, then `DataFrameSecurityValidator` before analysis.
- **Displaying comments**: `InputValidator` when accepting the comment and `XSSPrevention` when rendering it.


Example usage of the processor:
```python
from core.unicode_processor import UnicodeProcessor
cleaned = UnicodeProcessor.safe_encode_text(user_input)
```
