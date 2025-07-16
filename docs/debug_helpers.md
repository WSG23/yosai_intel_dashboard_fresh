# Debug Helpers

Several scripts are provided to assist with debugging the dashboard during development. These helpers are **not** required for normal operation but can be useful when diagnosing issues.

## Examples

- `examples/debug_live_upload.py` – validates the upload pipeline end to end.
- `examples/debug_chunked_analysis.py` – tests the chunked analytics flow.
- `examples/debug_deep_analytics.py` and `examples/deep_analytics_specific_debug.py` – inspect intermediate analytics data.
- `examples/unique_patterns_debug.py` – showcases unique pattern detection.

## Tools

- `tools/debug_dash_object.py` – dumps component properties for troubleshooting.
- Package `tools/debug/` – utilities for inspecting assets and callback registration.
- `scripts/debug_navbar_icons.py` – quick check for navigation icon rendering.
- `debug_cache_error.py` and `debug_mde.py` – standalone scripts for cache and markdown editor debugging.

Test stubs under `tests/utils/` and `tests/stubs/utils/` also provide simplified assets for debugging in the test suite.
