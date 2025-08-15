# Debug Helpers

Several scripts are provided to assist with debugging the dashboard during development. These helpers are **not** required for normal operation but can be useful when diagnosing issues.

## Tools

Standalone helper scripts that previously lived under `examples/` have been
removed. Use the following tools for diagnostics:

- `tools/debug_dash_object.py` – dumps component properties for troubleshooting.
- Package `tools/debug/` – utilities for inspecting assets and callback registration.
- `scripts/debug_navbar_icons.py` – quick check for navigation icon rendering.
- `scripts/validate_callback_system.py` – verifies callback dependencies.
- Run `python -m tools.debug` for a unified CLI covering asset and callback diagnostics.
- The old `debug_cache_error.py` and `debug_mde.py` helpers have been removed.

These helpers use your configured environment for secrets. Set `SECRET_KEY` in
your shell or secret manager before running them. The utilities no longer
inject a default value.

Test stubs under `tests/unit/utils/` and `tests/unit/stubs/utils/` also provide simplified assets for debugging in the test suite.
