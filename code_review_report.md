# Automated Code Review Report

Project: .


## Code Redundancy Analysis
Found 553 duplicate function signatures:
  - save_mappings(): 2 occurrences
  - __init__(self): 171 occurrences
  - upload_files(): 2 occurrences
  - clean_unicode_surrogates(text): 2 occurrences
  - get_ai_confidence_threshold(self): 8 occurrences

## Callback Analysis
Total callbacks found: 50
  - Pattern 'on[A-Z]\w+\s*=' appears in 19 files - consider consolidation
  - Pattern 'callback\s*=' appears in 10 files - consider consolidation
  - Pattern '\.subscribe\(' appears in 5 files - consider consolidation

## Unicode Handling
Found 715 potential encoding issues

## Python 3 Compliance
✗ Found Python 2 code that needs updating

## Security Scan Results
  - sql_injection: 31 instances
  - pickle_load: 3 instances
  - hardcoded_secret: 9 instances
  - exec_usage: 1 instances