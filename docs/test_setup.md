# Running the Test Suite

This project includes a fairly extensive set of unit and integration tests. The
steps below outline how to set up your environment and execute the entire suite.

## 1. Install Dependencies

Create and activate a virtual environment if you have not already:
```bash
python -m venv venv
source venv/bin/activate
```

Install the application and development requirements:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```
`requirements-dev.txt` includes additional packages such as **PyYAML** that are
required by the tests but not needed in production.

## 2. Prepare the Environment

Compile the translation files (needed for some integration tests):
```bash
pybabel compile -d translations
```

Copy the sample environment file and adjust any values you need:
```bash
cp .env.example .env
```

If the CSS bundle has not been built yet, generate it:
```bash
npm run build-css  # or python tools/build_css.py
```

## 3. Run the Tests

Execute the full suite with coverage reporting:
```bash
pytest --cov
```

Static analysis and linting checks can be run as well:
```bash
mypy .
flake8 .
black --check .
```

All tests are located under the `tests/` directory. Running `pytest` from the
repository root will automatically discover them.
