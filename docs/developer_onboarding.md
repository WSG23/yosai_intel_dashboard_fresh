# Developer Onboarding

This guide walks new contributors through setting up a local development environment for the Yōsai Intel Dashboard.

## Prerequisites

- **Python 3.11+**
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

3. **Install dependencies:**
   ```bash
   ./scripts/setup.sh
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env as needed
   ```

5. **(Optional) Initialize the database or load sample data.**
   Prepare your PostgreSQL database and populate it with any example data if desired.

6. **Run the test suite:**
   ```bash
   pytest --cov
   ```

7. **Start the application:**
   ```bash
   python app.py
   ```

The dashboard will be available at `http://127.0.0.1:8050` once the server starts.
