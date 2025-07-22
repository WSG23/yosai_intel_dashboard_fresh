# Running the Test Suite

The core test dependencies are listed in `requirements-test.txt` and can be installed with:

```bash
pip install -r requirements-test.txt
```

Some tests exercise features that rely on heavy optional packages. These extras are defined in `requirements-extra.txt` and are **not** required for the majority of the suite. Install them only when you need to run every test:

```bash
pip install -r tests/requirements-extra.txt
```

When the optional packages are missing, tests depending on them are automatically skipped.


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
