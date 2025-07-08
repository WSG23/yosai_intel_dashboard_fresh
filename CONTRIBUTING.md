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

See [docs/test_architecture.md](docs/test_architecture.md) for details on the
protocols used in tests and examples of injecting your own test doubles.

Please ensure tests and linters pass before opening a pull request.
