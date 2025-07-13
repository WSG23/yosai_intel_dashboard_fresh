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
pip install -r requirements.txt
pip install -r requirements-test.txt
```
Alternatively you can run `./scripts/setup.sh` to install the standard
dependencies. `requirements-test.txt` includes additional packages such as
**PyYAML** that are required by the tests but not needed in production.

### Required Python Packages

`requirements.txt` lists all core dependencies. The most important packages are:

- `Flask` and extensions (`Flask-Babel`, `Flask-Login`, `Flask-WTF`,
  `Flask-Compress`, `Flask-Talisman`, `Flask-Caching`)
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
