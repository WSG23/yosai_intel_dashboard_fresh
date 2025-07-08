# Testing Architecture

This project organizes tests into three layers to balance feedback speed with confidence.

## Unit Tests

Unit tests exercise individual functions or classes in isolation. External dependencies are replaced with **protocol-based fakes** to keep the tests fast and focused. A fake implements a minimal `Protocol` matching just the behaviour the unit under test relies on. No real network or disk access should occur in unit tests.

## Integration Tests

Integration tests verify that multiple components work together correctly. They use real implementations for most dependencies and may touch the filesystem, spawn background processes or run a web server. Integration tests are marked with `@pytest.mark.integration` so they can be included or excluded via pytest's `-m` flag.

## End‑to‑End (E2E) Tests

E2E tests drive the application through its user interface—typically with a headless browser via `dash_duo`. They provide the highest level of confidence but are slower to run. These tests also carry the `integration` mark and usually live alongside other integration tests.
