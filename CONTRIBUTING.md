# Contributing to Yōsai Intel Dashboard

Thank you for considering a contribution! Follow these steps to get the development environment ready.

## Setup

Install the core and development dependencies:

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
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
black --check .
bandit -r .
```

Please ensure tests and linters pass before opening a pull request.
