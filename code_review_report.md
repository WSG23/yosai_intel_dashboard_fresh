# Automated Code Review Report

Project: .
Files analyzed: 1057


## Code Redundancy Analysis
Total functions analyzed: 5184
Found 548 duplicate function signatures:
  - __init__(self): 146 occurrences
    • mde.py (removed):47
    • mapping/storage/base.py:31
  - get_ai_confidence_threshold(self): 6 occurrences
    • data_enhancer.py:84
    • config/dynamic_config.py:264
  - get_max_upload_size_mb(self): 10 occurrences
    • data_enhancer.py:87
    • config/dynamic_config.py:25
  - get_upload_chunk_size(self): 6 occurrences
    • data_enhancer.py:90
    • config/dynamic_config.py:279
  - __init__(self,max_size_mb,config): 5 occurrences
    • upload_validator.py:17
    • services/input_validator.py:20

## Modularity Assessment
Modular files: 682/1055

## Callback Analysis
Total callbacks found: 49
Callback distribution:
  - upload_validator.py: 1 callbacks
  - core/dash_profile.py: 1 callbacks
  - core/config.py: 1 callbacks
  - core/truly_unified_callbacks.py: 1 callbacks
  - Pattern 'on[A-Z]\w+\s*=' appears in 19 files - consider consolidation
  - Pattern 'callback\s*=' appears in 10 files - consider consolidation
  - Pattern '\.subscribe\(' appears in 5 files - consider consolidation

## Unicode Handling
Found 702 potential encoding issues
  - test_base_services.py:6 - Potential encoding issue: str(PROJECT_ROOT))
  - mde.py (removed):12 - Potential encoding issue: str(PROJECT_ROOT))
  - mde.py (removed):262 - Potential encoding issue: str(e)}", color="danger")
  - mde.py (removed):389 - Potential encoding issue: str(e)}", color="warning")
  - upload_endpoint.py:40 - Potential encoding issue: .decode()
✓ 90 files use proper UTF-8 encoding

## Python 3 Compliance
✗ Found Python 2 code that needs updating:
  - plugins/compliance_plugin/api.py:
    • Line 32: print_statement - print =
  - plugins/compliance_plugin/compliance_controller.py:
    • Line 26: print_statement - print f
    • Line 675: print_statement - print f
  - file_processing/data_processor.py:
    • Line 162: print_statement - print o
  - tests/test_consolidated_learning_service.py:
    • Line 32: print_statement - print =
    • Line 134: print_statement - print =
    • Line 136: print_statement - print i

## API Analysis
Total API endpoints found: 18
API files:
  - debug_route.py: 1 endpoints
  - plugins/compliance_plugin/tests/test_compliance_framework.py: 1 endpoints
  - plugins/compliance_plugin/services/compliance_csv_processor.py: 1 endpoints
  - plugins/compliance_plugin/services/toggle_manager.py: 5 endpoints

## Security Scan Results
⚠️  Found 46 potential security issues:
  - sql_injection: 38 instances
  - hardcoded_secret: 7 instances
    • tests/session_tests/test_session_lifetime.py:68
  - exec_usage: 1 instances
    • independent_tests/test_page_container_layout.py:19

## Performance Analysis
Found 109 potential performance issues:
  - string_concatenation: 33 instances
  - nested_loops: 37 instances
  - large_list_comp: 9 instances
  - no_generator: 30 instances

## Summary
- Files analyzed: 1057
- Total functions: 5184
- Duplicate functions: 548
- Security issues: 46
- Performance issues: 109
- Python 3 compliant: No