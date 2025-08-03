# Running the Test Suite

**Important**: install the test dependencies **before** invoking `pytest` so that
all helper modules can be imported. Use one of the commands below:

```bash
pip install -r requirements-test.txt
```

This installs mandatory dependencies such as `PyYAML`, `psutil` and `pandas`
used by `tests/conftest.py`.

Or run the helper script:

```bash
scripts/setup_tests.sh
```

Some tests exercise features that rely on heavy optional packages. These extras are defined in `requirements-extra.txt` and are **not** required for the majority of the suite. Install them only when you need to run every test:

```bash
pip install -r tests/requirements-extra.txt
```

When the optional packages are missing, tests depending on them are automatically skipped.

## Test Configuration

The test environment is initialised by `tests/config.py`. Importing this module
adds the project root to `sys.path`, sets a few required environment variables
and registers lightweight stubs for optional dependencies like `hvac`,
`cryptography` and `boto3`. `tests/conftest.py` loads it automatically so the
fixtures it exposes (for example `fake_unicode_processor` and `temp_dir`) are
available to all tests.

## Database Fixtures

`tests/conftest.py` also provides database connection factories for common
backends. Each fixture yields a callable that returns a connection wrapped in a
context manager. Acquire and release connections using the `with` statement:

```python
def test_example(sqlite_connection_factory):
    with sqlite_connection_factory() as conn:
        conn.execute_query("SELECT 1")
```

Available fixtures:

* `mock_db_factory` – in-memory mock database.
* `sqlite_connection_factory` – SQLite database stored in a temporary file.
* `postgres_connection_factory` – PostgreSQL database started with
  `testcontainers` (skipped if the dependency is missing).

Connections are automatically returned to their pools on context exit and pools
are cleaned up when the test finishes.

## Migrating Test Imports

The helper script `tools/migrate_tests.py` updates test files to use the
current import layout and adds `pytest.importorskip()` checks for optional
dependencies. Run it in dry‑run mode to preview edits:

```bash
python tools/migrate_tests.py --dry-run
```

Remove the flag to apply changes to the repository:

```bash
python tools/migrate_tests.py
```

`tests/config.py` enables the lightweight service mode by default so heavy
dependencies are stubbed out. Run the suite with:

```bash
pytest
```

## Query Count Checks

The analytics retrieval layer is covered by tests that verify the number of SQL
statements executed. These tests use the `query_recorder` fixture and fail when
more queries than expected are issued.

Run them with:

```bash
pytest tests/database/test_query_limits.py
```

## Load Testing

A standalone script exercises the event processing pipeline. It relies on
`aiohttp` to issue HTTP requests, so install it first:

```bash
pip install aiohttp
```

Run the load test with:

```bash
python tests/performance/test_event_processing.py
```

The script targets the gateway at `http://localhost:8081`.

## Kafka Load Test

Another script, `tools/load_test.py`, publishes synthetic events to Kafka and
calculates throughput from Prometheus metrics. The Makefile exposes a helper
target so the stack can be exercised easily:

```bash
make load-test
```

Optional variables allow adjusting brokers, Prometheus URL, event rate and test
duration:

```bash
make load-test RATE=100 DURATION=30
```

Ensure the Docker Compose stack is running so Kafka and Prometheus are
available. The command prints a JSON summary which is also saved by the CI
performance job as an artifact.
