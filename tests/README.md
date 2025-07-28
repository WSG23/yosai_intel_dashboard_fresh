# Running the Test Suite

**Important**: install the test dependencies **before** invoking `pytest` so that
all helper modules can be imported. Use one of the commands below:

```bash
pip install -r requirements-test.txt
```

Or run the helper script:

```bash
scripts/setup_tests.sh
```

Some tests exercise features that rely on heavy optional packages. These extras are defined in `requirements-extra.txt` and are **not** required for the majority of the suite. Install them only when you need to run every test:

```bash
pip install -r tests/requirements-extra.txt
```

When the optional packages are missing, tests depending on them are automatically skipped.

Before running the suite locally, enable the lightweight service mode so heavy
dependencies are stubbed out:

```bash
export LIGHTWEIGHT_SERVICES=1
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
