# Migration from Legacy Unicode Utilities

The Yōsai Intel Dashboard now relies on the standalone `unicode_toolkit`
library for all Unicode handling.  The previous `core.unicode` module
remains as a compatibility layer but will be removed in a future release.
`unicode_toolkit` provides hardened text utilities, DataFrame
sanitization helpers and SQL encoding functions.

## Quick Migration Reference

### Text Processing Migration
```python
from core.unicode import UnicodeProcessor, UnicodeSecurityProcessor

result = UnicodeProcessor.clean_text(text)


# Security-sensitive contexts
secure = sanitize_input(text)
```

### SQL Processing Migration
```python
from unicode_toolkit import SQLProcessor
safe_query = SQLProcessor.encode_query(query)
safe_params = SQLProcessor.encode_params(params)
```

### DataFrame Processing Migration
```python
from unicode_toolkit import sanitize_dataframe
clean_df = sanitize_dataframe(df, progress=True)
```

### Unified Handler
```python
from config.unicode_handler import UnicodeHandler

handler = UnicodeHandler()
safe_query = handler.encode_query(query)
clean_name = handler.clean_filename("data\ud800.csv")
```

### Using `unicode_toolkit`

Install the library with `pip install unicode_toolkit` and replace old
imports with the new module:

| Legacy API | New API |
|------------|---------|
| `UnicodeProcessor.safe_encode` | `unicode_toolkit.safe_encode` |
| `UnicodeProcessor.safe_decode` | `unicode_toolkit.safe_decode` |
| `UnicodeTextProcessor.clean_text` | `unicode_toolkit.clean_text` |
| `UnicodeSQLProcessor.encode_query` | `unicode_toolkit.SQLProcessor.encode_query` |
| `sanitize_dataframe` | `unicode_toolkit.sanitize_dataframe` |
| `UnicodeSecurityProcessor.sanitize_input` | `unicode_toolkit.sanitize_input` |

Examples with the new API:

```python
from unicode_toolkit import TextProcessor, SQLProcessor, sanitize_dataframe

processor = TextProcessor()
clean = processor.clean(text)
safe_query = SQLProcessor.encode_query(query)
clean_df = sanitize_dataframe(df)
```

## Detailed Migration Steps

### Step 1: Identify Legacy Usage
Run `python tools/audit_unicode_usage.py` to list files that still import
`core.unicode`. These modules should be updated to use `unicode_toolkit`.
### Step 2: Update Import Statements
### Step 3: Update Function Calls
### Step 4: Test Migration
### Step 5: Remove Deprecated Imports

### Common Migration Patterns
### Migration Validation Tools
### Performance Improvements
### Security Enhancements

REQUIREMENTS:
- Complete migration examples for every legacy function
- Step-by-step migration procedures
- Automated detection tools
- Validation scripts
- Performance comparison data
- Security improvement documentation


### Error Handling Migration
Use `core.error_handling` for unified decorators and circuit breakers. Replace custom @app.errorhandler code with `register_error_handlers` and wrap functions with `with_error_handling`.
