# Contributing to Yōsai Intel Dashboard

Thank you for considering a contribution! Follow these steps to get the development environment ready.

## Setup

Install the core and development dependencies along with the packages
required for running the tests:

```bash
./scripts/setup.sh
pip install -r requirements-test.txt
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

The unit test suite requires additional packages specified in
`requirements-test.txt`. Install them prior to running the tests:

```bash
./scripts/install_test_deps.sh
```

Alternatively you can run `pip install -r requirements-test.txt` directly.

## Running Tests

After installing the dependencies (including those from
`requirements-test.txt`) you can run the tests and code quality checks:

```bash
pytest
mypy --strict .
flake8 .
isort --check .
black --check .
bandit -r .
```

Run `isort .` to automatically sort imports before committing changes.

### Database Query Helpers

When executing SQL, always acquire connections using the factory context manager:

```python
with factory.get_connection() as conn:
    execute_query(conn, sql)
```

Direct calls like `execute_query(factory.get_connection(), ...)` are flagged by
a custom linter that runs via `make lint` and `pytest`.

See [docs/test_architecture.md](docs/test_architecture.md) and
[docs/testing_with_protocols.md](docs/testing_with_protocols.md) for details on
the testing protocols, container builder and available test doubles.

Please ensure tests and linters pass before opening a pull request.

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
from services.analytics import AnalyticsService
from config.settings import Settings

# New (correct)
from yosai_intel_dashboard.src.core.domain.entities.user import User
from yosai_intel_dashboard.src.services.analytics import AnalyticsService
from yosai_intel_dashboard.src.infrastructure.config.settings import Settings
```

Run `isort .` to automatically sort imports before committing changes.

## Developer Guides

Refer to [docs/developer_guides.rst](docs/developer_guides.rst) for instructions on
the test migration script and reviewing any items flagged as ``needs manual review``.
