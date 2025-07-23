# Automated Code Review Report

Project: .
Files analyzed: 1044


## Code Redundancy Analysis
Total functions analyzed: 5094
Found 553 duplicate function signatures:
  - save_mappings(): 2 occurrences
    • mappings_endpoint.py:55
    • archive/legacy_backend/backend/app.py:151
  - __init__(self): 171 occurrences
    • mde.py:48
    • mapping/storage/base.py:31
  - upload_files(): 2 occurrences
    • upload_endpoint.py:21
    • archive/legacy_backend/backend/app.py:49
  - clean_unicode_surrogates(text): 2 occurrences
    • data_enhancer.py:94
    • core/unicode.py:434
  - get_ai_confidence_threshold(self): 8 occurrences
    • data_enhancer.py:80
    • archive/mvp/mvp_data_enhance.py:63

## Modularity Assessment
Modular files: 672/1042
Files with long functions (>50 lines):
  - examples/debug_deep_analytics.py: avg 222.0 lines/function
  - examples/diagnostic_script.py: avg 222.0 lines/function
  - examples/unique_patterns_debug.py: avg 217.0 lines/function
  - device_endpoint.py: avg 77.0 lines/function
  - tools/cli_examine_mapping_content.py: avg 73.0 lines/function

## Callback Analysis
Total callbacks found: 50
Callback distribution:
  - upload_validator.py: 1 callbacks
  - core/dash_profile.py: 1 callbacks
  - core/callback_controller.py: 1 callbacks
  - core/truly_unified_callbacks.py: 1 callbacks
  - core/theme_manager.py: 1 callbacks
  - Pattern 'on[A-Z]\w+\s*=' appears in 19 files - consider consolidation
  - Pattern 'callback\s*=' appears in 10 files - consider consolidation
  - Pattern '\.subscribe\(' appears in 5 files - consider consolidation

## Unicode Handling
Found 715 potential encoding issues
  - mappings_endpoint.py:30 - Potential encoding issue: str(exc))
  - mappings_endpoint.py:32 - Potential encoding issue: str(exc))
  - mappings_endpoint.py:50 - Potential encoding issue: str(exc))
  - mappings_endpoint.py:52 - Potential encoding issue: str(exc))
  - mappings_endpoint.py:92 - Potential encoding issue: str(e))
✓ 92 files use proper UTF-8 encoding

## Python 3 Compliance
✗ Found Python 2 code that needs updating:
  - code_analyzer.py:
    • Line 492: print_statement - print r
  - archive/legacy_backend/backend/app.py:
    • Line 45: print_statement - print f
    • Line 62: print_statement - print
                w
    • Line 65: print_statement - print =
  - plugins/compliance_plugin/api.py:
    • Line 32: print_statement - print =
  - plugins/compliance_plugin/compliance_controller.py:
    • Line 25: print_statement - print f
    • Line 674: print_statement - print f
  - file_processing/data_processor.py:
    • Line 162: print_statement - print o

## API Analysis
Total API endpoints found: 39
API files:
  - investor_demo_interface.py: 4 endpoints
  - debug_route.py: 1 endpoints
  - archive/mvp/investor_demo_interface.py: 4 endpoints
  - archive/mvp/mvp_web_interface.py: 2 endpoints
  - archive/legacy_backend/backend/app_main.py: 7 endpoints

## Security Scan Results
⚠️  Found 44 potential security issues:
  - sql_injection: 31 instances
    • code_analyzer.py:252
    • database/index_optimizer.py:50
  - pickle_load: 3 instances
    • tools/migrate_pickle_mappings.py:41
    • core/plugins/config/cache_manager.py:118
  - hardcoded_secret: 9 instances
    • yosai-assessment/code-quality-analyzer.py:17
    • config/config_transformer.py:36
  - exec_usage: 1 instances
    • independent_tests/test_page_container_layout.py:19

## Performance Analysis
Found 100 potential performance issues:
  - string_concatenation: 33 instances
  - large_list_comp: 7 instances
  - nested_loops: 29 instances
  - no_generator: 31 instances

## Summary
- Files analyzed: 1044
- Total functions: 5094
- Duplicate functions: 553
- Security issues: 44
- Performance issues: 100
- Python 3 compliant: No