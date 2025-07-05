# Migration from Legacy Unicode Utilities

The Yōsai Intel Dashboard has consolidated all Unicode processing into a centralized,
modular system under `core.unicode`. This migration eliminates security vulnerabilities
and provides specialized processors for different contexts.

## Quick Migration Reference

### Text Processing Migration
```python
# OLD (DEPRECATED):
from utils.unicode_utils import sanitize_unicode_input
from utils.unicode_utils import clean_unicode_text
from utils.unicode_utils import handle_surrogate_characters

# NEW (RECOMMENDED):
from core.unicode import UnicodeTextProcessor
processor = UnicodeTextProcessor()
result = processor.clean_text(text)

# OR for security contexts:
from core.unicode import UnicodeSecurityProcessor
result = UnicodeSecurityProcessor.sanitize_input(text)
```

### SQL Processing Migration
```python
# OLD (DEPRECATED):
from config.unicode_handler import safe_encode_query
from utils.unicode_utils import safe_encode

# NEW (RECOMMENDED):
from core.unicode import UnicodeSQLProcessor
safe_query = UnicodeSQLProcessor.encode_query(query)
```

### DataFrame Processing Migration
```python
# OLD (DEPRECATED):
from utils.unicode_utils import sanitize_dataframe
from security.unicode_security_handler import sanitize_dataframe

# NEW (RECOMMENDED):
from core.unicode import sanitize_dataframe
clean_df = sanitize_dataframe(df, progress=True)
```

## Detailed Migration Steps

### Step 1: Identify Legacy Usage
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

