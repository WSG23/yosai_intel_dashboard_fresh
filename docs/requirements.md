# Python requirements

The project uses two requirement files to manage Python dependencies.

- `requirements.txt` – core runtime packages required for the application and services.
- `requirements-dev.txt` – includes `-r requirements.txt` and adds development and testing tools.

Install the base dependencies with:

```bash
pip install -r requirements.txt
```

For development or running the test suite install the extended set:

```bash
pip install -r requirements-dev.txt
```

These files replace older service-specific requirement lists that caused version drift.
Add new dependencies to one of them as appropriate.
