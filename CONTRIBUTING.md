# Contributing to Yōsai Intel Dashboard

Thank you for considering a contribution! Follow these steps to get the development environment ready.

## Setup

Install the core and development dependencies:

```bash
./scripts/setup.sh
npm install
pip install pre-commit
pre-commit install
```

These additional packages provide linting, type checking, security scanning and testing tools used in our CI pipeline.

## Running Tests

After installing the dependencies you can run the tests and code quality checks:

```bash
pytest
mypy --strict .
flake8 .
isort --check .
black --check .
bandit -r .
```

Run `isort .` to automatically sort imports before committing changes.

Please ensure tests and linters pass before opening a pull request.

## Test Guidelines

* **Unit tests** should rely on protocol-based fakes for all dependencies. This
  keeps them fast and ensures the test only depends on behaviour defined in a
  `Protocol`.
* **Integration and E2E tests** may use real services such as the database or a
  running web server. Mark these tests with `@pytest.mark.integration` so they
  can be selected with `-m integration` or skipped when running only unit tests.
