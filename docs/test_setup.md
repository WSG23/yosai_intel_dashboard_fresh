# Running the Test Suite

This project includes a fairly extensive set of unit and integration tests. The
steps below outline how to set up your environment and execute the entire suite.

## 1. Install Dependencies

Create and activate a virtual environment if you have not already:
```bash
python -m venv venv
source venv/bin/activate
```

Install the application and test requirements **before** running any tests:
```bash
pip install -r requirements-dev.txt
```
Alternatively you can run `./scripts/setup.sh` to install the standard
dependencies along with the test requirements. `requirements-dev.txt`
includes additional packages such as **PyYAML** that are required by the
tests but not needed in production.

### Required Python Packages

`requirements.txt` lists all core dependencies. The most important packages are:

- `Flask` and extensions (`Flask-Babel`, `Flask-Login`, `Flask-WTF`,
  `Flask-Talisman`, `Flask-Caching`)
- `dash`, `dash-bootstrap-components`, `dash-extensions`, `dash-leaflet`
- `plotly`
- `pandas`, `numpy`
- `authlib`, `python-jose`
- `cssutils`
- `scipy`, `scikit-learn`, `joblib`
- `psutil`
- `psycopg2-binary`
- `requests`
- `sqlparse`, `bleach`
- `PyYAML`
- `flasgger`
- `python-dotenv`
- `pytest`
- `pyarrow`, `polars`
- `gunicorn`
- `chardet`
- `pyopenssl`
- `SQLAlchemy`

Some pages rely on optional packages. For example, the upload and analytics
pages require **pandas** to manipulate CSV files. The monitoring endpoint uses
**psutil** for CPU and memory metrics, while the file processing utilities
depend on **chardet** to detect text encoding. Ensure these packages remain
installed if you intend to use those features.

Install the Node dependencies used for building CSS and running accessibility
checks:
```bash
npm install
```

## 2. Prepare the Environment

Compile the translation files (needed for some integration tests):
```bash
pybabel compile -d translations
```

Copy the sample environment file and adjust any values you need:
```bash
cp .env.example .env
```
`setup_dev_mode` expects `DB_PASSWORD` to be set. The example `.env.example`
already defines a placeholder. If you skip this variable the tests will only
show a warning but any database-dependent checks may fail.

`SECRET_KEY` is **mandatory**. If it is missing the API initialization fails
with a `RuntimeError` when the tests create the application context. When
running the test suite you can supply a custom value through the
`TEST_SECRET_KEY` environment variable instead of setting `SECRET_KEY`
directly.

If the CSS bundle has not been built yet, generate it:
```bash
npm run build-css  # or python tools/build_css.py
```

### Make the Package Importable

The tests rely on absolute imports such as `services.resilience`. Ensure the
repository root is on `PYTHONPATH` or install the project in editable mode:

```bash
pip install -e .
```

The module `tests/config.py` – loaded automatically by `pytest` – appends the
project root to `sys.path`, sets minimal environment variables and registers
lightweight stubs for optional dependencies. It reads `TEST_SECRET_KEY` and
`TEST_API_TOKEN` from the environment to populate the `SECRET_KEY` and
`API_TOKEN` variables used during testing, falling back to dynamically generated
defaults when they are absent. Importing it manually is rarely necessary, but it
can be handy when running individual files.

`tests.unit.infrastructure.TestInfrastructure.setup_environment()` performs a similar
bootstrapping step for integration tests. It appends the `tests/unit/stubs`
directory to `sys.path` and injects stub modules such as `pyarrow`, `pandas` and
`numpy` into `sys.modules` when they are missing. New stubs can be provided by
dropping a module or package into `tests/unit/stubs` or by calling
`tests.unit.infrastructure.mock_factory.stub("name")` inside a test.

Without one of these steps you may encounter `ModuleNotFoundError` during test
collection.

## 3. Run the Tests

Execute the full suite with coverage reporting. `tests/config.py` enables the
lightweight service implementations so heavy optional dependencies are not
required:
```bash
pytest --cov --cov-fail-under=80
```

### Deterministic Test Order

The test suite employs [`pytest-randomly`](https://pypi.org/project/pytest-randomly/)
to shuffle tests while keeping results reproducible. A fixed seed of `1234` is
configured in `pytest.ini` so failures can be replicated exactly.

### Network Isolation

The test suite uses [`pytest-socket`](https://pypi.org/project/pytest-socket/)
to prevent outbound network calls. `pytest.ini` enables `--disable-socket` and
allows only `localhost` and `127.0.0.1` via `--allow-hosts`. External hosts must
not be contacted; if a test requires network access it should mock the
interaction instead of performing a real request.

### Memory Profiling

The test suite integrates [`memory_profiler`](https://pypi.org/project/memory-profiler/)
to record the peak memory usage of each test and enforces a process-level memory
cap. By default each test is limited to **512 MB** of address space. You can
override this limit for the entire run by setting the `PYTEST_MAX_MEMORY_MB`
environment variable:

```bash
PYTEST_MAX_MEMORY_MB=1024 pytest
```

Individual tests may specify a different limit using the `@pytest.mark.memlimit` marker:

```python
@pytest.mark.memlimit(256)
def test_something():
    ...
```

When `memory_profiler` is installed, each test will log its starting and ending
memory usage, helping track leaks or unexpectedly large allocations.

Before invoking the lint task you must ensure the Node packages are installed:
```bash
npm install
```

Static analysis and linting checks can be run as well:
```bash
mypy .
flake8 .
black --check .
```

All tests are located under the `tests/` directory. Running `pytest` from the
repository root will automatically discover them.
