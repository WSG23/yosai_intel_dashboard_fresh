# Developer Setup Checklist

This checklist summarizes the basic steps required to prepare a development environment.

## IDE Configuration

### Visual Studio Code
1. Install the Python extension.
2. Set a vertical ruler at **88** characters:
   - Add the following to your settings: `"editor.rulers": [88]`.
3. Use **Black** as the default formatter and enable "Format on Save".

### PyCharm
1. Open **Preferences** ➜ **Editor** ➜ **Code Style** ➜ **Python**.
2. Set the **Right Margin** to **88**.
3. Install the **Black** plugin (or add it as an external tool) and enable it as the formatter.

## Pre‑commit Hooks
1. Install the dependencies (including test packages) and `pre-commit`:
   ```bash
   ./scripts/setup.sh
   pip install pre-commit
   ```
2. Install the hooks:
   ```bash
   pre-commit install
   ```
3. Run all hooks manually with:
   ```bash
   pre-commit run --all-files
   ```

## Verify Formatting and Linting
Run the following before committing changes:
```bash
black --check .
flake8 .
isort --check .
mypy --strict .
```
These commands ensure consistent code style and pass the linting rules used in CI.
