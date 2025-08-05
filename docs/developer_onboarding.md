# Developer Onboarding

This guide walks new contributors through setting up a local development environment for the Yōsai Intel Dashboard.

## Prerequisites

- **Python 3.8+**
- **PostgreSQL 13+**
- **Redis**

## Setup Steps

1. **Clone the repository:**
   ```bash
   git clone <repository>
   cd yosai_intel_dashboard
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install Python dependencies:**
   ```bash
   ./scripts/setup.sh
   ```
   This installs `requirements.txt` and `requirements-dev.txt`. The
   development requirements include additional packages such as **PyYAML**
   that are necessary when running the test suite.

4. **Install Node dependencies:**
   ```bash
   npm install
   ```
   These PostCSS packages are required when building the CSS bundle.
5. **Compile translations:**
   ```bash
   pybabel compile -d translations
   ```

6. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env as needed
   ```
   The development helper `setup_dev_mode` expects `DB_PASSWORD` to be
   defined. The placeholder value in `.env.example` is sufficient for a
   local setup. If you omit it the app only emits a warning but database
   features may not be available.

   `SECRET_KEY` **must** also be set. The API exits with a
   `RuntimeError` if this variable is missing.

7. **(Optional) Initialize the database or load sample data.**
   Prepare your PostgreSQL database and populate it with any example data if desired.

8. **Run the test suite:**
   ```bash
   pytest --cov
   mypy .
   flake8 .
   black --check .
   ```
   
9. **Start the application:**
   Use the unified entry point which warms caches before launching the server.
   ```bash
   python start_api.py
   ```

The dashboard will be available at `http://127.0.0.1:8050` once the server starts.
