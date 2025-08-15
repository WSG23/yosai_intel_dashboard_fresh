# Contributing to Yōsai Intel Dashboard

Thank you for considering a contribution! For a full walkthrough of the development environment using Docker or local processes, see [docs/getting-started.md](docs/getting-started.md). Follow these steps to get the development environment ready.

Before you start, review the repository [Project Layout](README.md#project-layout) to orient yourself to key directories.
For details on unified callback registration and security validation, see
[docs/callbacks.md](docs/callbacks.md).

## Setup

Install the core and development dependencies:

```bash
./scripts/setup.sh
npm install
pip install pre-commit
pre-commit install
```

The hook will automatically run each time you commit. To verify all files at
once execute:

```bash
pre-commit run --all-files
```

These additional packages provide linting, type checking, security scanning and testing tools used in our CI pipeline.

## Installing Test Dependencies

The unit test suite relies on packages included in
`requirements-dev.txt`. Install them prior to running the tests if you
have not already run the setup script:

```bash
./scripts/install_test_deps.sh
```

## Running Tests

After installing the dependencies (including those from
`requirements-dev.txt`) you can run the quick test suite and code quality checks:

```bash
pytest -m "not slow"
mypy --strict .
flake8 .
isort --check .
black --check .
bandit -r .
```

To execute the slower tests that start Docker containers for Postgres, Kafka,
and Redis use:

```bash
pytest -m slow
```

Run `isort .` to automatically sort imports before committing changes.

### Docstring Style

Use Google-style docstrings for all new Python code. The [pydocstyle](https://pypi.org/project/pydocstyle/)
pre-commit hook enforces this convention and runs in CI. A basic example:

```python
def add(a: int, b: int) -> int:
    """Add two numbers.

    Args:
        a: First value.
        b: Second value.

    Returns:
        The sum of ``a`` and ``b``.
    """
    return a + b
```

API reference documentation is generated with [mkdocs](https://www.mkdocs.org/) and
[mkdocstrings](https://mkdocstrings.github.io/). Build the docs locally with:

```bash
mkdocs build
```

When creating a new module, include a module-level docstring and at least one
usage example in public function docstrings. These examples appear in the
generated API reference and help others understand how to use your code.

### Database Query Helpers

When executing SQL, always acquire connections using the factory context manager:

```python
with factory.get_connection() as conn:
    execute_query(conn, sql)
```

Direct calls like `execute_query(factory.get_connection(), ...)` are flagged by
a custom linter that runs via `make lint` and `pytest`.

### SQL Query Safety

New SQL queries must use parameterized statements. Before committing, scan
modified Python files for unsafe string interpolation:

```bash
PYTHONPATH=. python scripts/sql_migration_report.py <changed files>
PYTHONPATH=. python scripts/detect_sql_strings.py <changed files>
```

The CI pipeline runs the same scripts on pull requests and will fail if they
detect concatenated or interpolated SQL strings.

See [docs/test_architecture.md](docs/test_architecture.md) and
[docs/testing_with_protocols.md](docs/testing_with_protocols.md) for details on
the testing protocols, container builder and available test doubles.

Please ensure tests and linters pass before opening a pull request.

### Test Types and Expected Runtime

| Type | Description | Approx. runtime | Command |
| ---- | ----------- | --------------- | ------- |
| Unit tests | No external services, network and file I/O are mocked. | < 5 minutes | `pytest -m "not slow"` |
| Slow tests | Spin up ephemeral services (Kafka, Postgres, Redis) via Docker. Skipped when Docker is unavailable. | ~10 minutes | `pytest -m slow` |

## Dependency Updates

Automated pull requests labeled `deps` are created by Dependabot to keep
dependencies current. Maintainers review these weekly and merge them once
continuous integration checks succeed.

## Generating Protobuf Code

Protobuf service definitions live under `proto/`. When the `.proto` files
change, regenerate the language specific sources using the Makefile helpers:

```bash
make proto-python   # build Python stubs
make proto-go       # build Go stubs
make proto-all      # run both
```

Commit the resulting generated files so CI can verify they are up to date.

## Clean Architecture Structure

This project follows Clean Architecture principles. When contributing:

### Directory Structure
- `yosai_intel_dashboard/src/core/` - Business logic (no external dependencies)
- `yosai_intel_dashboard/src/adapters/` - Interface adapters (API, UI)
- `yosai_intel_dashboard/src/infrastructure/` - Frameworks and tools
- `yosai_intel_dashboard/src/services/` - Application services

### Import Guidelines
Use the new import paths:
```python
# Old (deprecated)
from models.user import User
from yosai_intel_dashboard.src.services.analytics import AnalyticsService
from yosai_intel_dashboard.src.infrastructure.config.settings import Settings

# New (correct)
from yosai_intel_dashboard.src.core.domain.entities.user import User
from yosai_intel_dashboard.src.services.analytics import AnalyticsService
from yosai_intel_dashboard.src.infrastructure.config.settings import Settings
```

Run `isort .` to automatically sort imports before committing changes.

## Developer Guides

Refer to [docs/developer_guides.rst](docs/developer_guides.rst) for instructions on
the test migration script and reviewing any items flagged as ``needs manual review``.
