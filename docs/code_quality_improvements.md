# Code Quality Improvements

This repository enforces a strict import ordering scheme. The ordering is managed
by [isort](https://pycqa.github.io/isort/) using the profile defined in
`.isort.cfg`.
Imports are grouped as `FUTURE`, `STDLIB`, `THIRDPARTY`, `FIRSTPARTY` and
`LOCALFOLDER` to keep dependencies and application code clearly separated.

Several additional tools are configured through `pre-commit`:

- **Black** – formats Python code
- **isort** – sorts imports
- **Flake8** – enforces style rules
- **Mypy** – performs static type checking
- **Bandit** – detects security issues

Imports can also be reorganized in bulk by running `scripts/organize_imports.py`.

Install the hooks once and run them manually with:

```bash
pre-commit install
pre-commit run --all-files
```
