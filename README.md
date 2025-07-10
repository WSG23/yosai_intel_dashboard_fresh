# Yōsai Intel Dashboard

An AI-powered modular security intelligence dashboard for physical access control monitoring.

## Architecture Overview

This project follows a fully modular design built around a dependency injection container.  Detailed diagrams explain how the pieces fit together:

- [Architecture](docs/architecture.md)
- [Data Flow](docs/data_flow.md)
- [System Diagram](docs/system_diagram.md)
- [Deployment Diagram](docs/deployment_diagram.md)
- [Analytics Upload Sequence](docs/analytics_sequence.md)
- [Roadmap](docs/roadmap.md)
- [Sequence Diagrams](docs/sequence_diagrams.md)
- [UI Flows](docs/ui_flows.md)
- [Upload Interface Guide](docs/upload_interface.md)
- [UI Design Assets](docs/ui_design/README.md)
- [Validation Overview](docs/validation_overview.md)
- [Model Cards](docs/model_cards.md)
- [Data Versioning](docs/data_versioning.md)
- [Data Processing](docs/data_processing.md)
- [Testing Architecture](docs/test_architecture.md)

Core service protocols live in `services/interfaces.py`. Components obtain
implementations from the `ServiceContainer` when an explicit instance is not
provided, allowing tests to supply lightweight mocks.

The dashboard is extensible through a lightweight plugin system. Plugins live in the `plugins/` directory and are loaded by a `PluginManager`. See [docs/plugins.md](docs/plugins.md) for discovery, configuration details and a simple **Hello World** example. The [plugin lifecycle diagram](docs/plugin_lifecycle.md) illustrates how plugins are discovered, dependencies resolved and health checks performed.

```
yosai_intel_dashboard/
├── app.py                     # Main application entry point
├── config/                    # Configuration management
│   ├── config.py              # Unified configuration loader
│   ├── database_manager.py    # Database connections and pooling
│   └── cache_manager.py       # Simple cache interface
├── models/                    # Data models and business entities
│   ├── base.py               # Base model classes
│   ├── entities.py           # Core entities (Person, Door, Facility)
│   ├── events.py             # Event models (AccessEvent, Anomaly)
│   ├── enums.py              # Enumerated types
│   └── access_events.py      # Access event operations
├── services/                  # Business logic layer
│   └── analytics_service.py  # Analytics and data processing
├── components/               # UI components
│   ├── analytics/            # Analytics-specific components
│   ├── ui/                   # Shared UI components
│   └── map_panel.py          # Map visualization
├── pages/                    # Multi-page application pages
│   └── deep_analytics.py     # Analytics page
├── utils/                    # Utility functions
└── assets/                   # Static assets and CSS
    └── css/                  # Modular CSS architecture
```

### Navbar Icons

Store PNG images for the navigation bar in `assets/navbar_icons/`. The
application expects the following files:

* `dashboard.png`
* `analytics.png`
* `graphs.png`
* `upload.png`
* `print.png`
* `settings.png`
* `logout.png`

Additional icons can live in the same directory as long as their paths match the references in
`components/ui/navbar.py`.

Run the debug helper to verify that icon files exist and can be served:

```bash
python -m tools.debug assets
```
Pass icon names after the command to check custom files.

## 🚀 Quick Start

### Development Setup

Python 3.8 or later is required. All pinned dependency versions are compatible
with this Python release and newer.

1. **Clone and enter the project:**
   ```bash
   git clone <repository>
   cd yosai_intel_dashboard
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies:**
   ```bash
   ./scripts/setup.sh
   ```
   The script installs both `requirements.txt` and `requirements-dev.txt` from
   PyPI (or a local `packages/` directory if present) and runs `npm install` to
   fetch Node dependencies. Ensure dependencies are installed **before** running
   Pyright or using the Pylance extension. Missing packages will otherwise
   appear as unresolved imports.

4. **Install Node dependencies (optional):**
   PostCSS and other build tools live in `package.json`. `./scripts/setup.sh`
   already runs `npm install`, but you can execute it manually if desired.
   ```bash
   npm install
   ```
5. **Set up environment:**
   ```bash
   cp .env.example .env
   # Generate random development secrets
   python scripts/generate_dev_secrets.py >> .env
   # Edit .env with your configuration (e.g. set HOST and database info)
   ```
6. **Build the CSS bundle:**
   Ensure `node` and `npm` are available if you use the npm command.
   ```bash
   npm run build-css  # or `python tools/build_css.py`
   ```
   The command generates `assets/dist/main.css`, `assets/dist/main.min.css` and
   `assets/dist/main.min.css.map`. These files are auto-generated and should not
   be edited directly. Modify source files under `assets/css/` and rerun the
   build when needed.

7. **Run the application (development only):**
   The app now loads variables from `.env` automatically.
   ```bash
   python app.py  # use only for local development
   ```
   For production deployments start a WSGI server instead:
   ```bash
   gunicorn wsgi:server
   # or
   uwsgi --module wsgi:server
   ```
8. **Access the dashboard:**
   Open http://127.0.0.1:8050 in your browser. The application runs over
   plain HTTP by default; configure a reverse proxy with TLS if you need HTTPS.
   The development server does not support HTTPS, so be sure to visit
   `http://<host>:<port>` rather than `https://` when testing locally.
   Using an HTTPS URL will produce "Bad request version" errors because the
   built-in server is not configured for TLS.

## Developer Onboarding

For a more detailed walkthrough of the environment setup and testing workflow,
see [developer_onboarding.md](docs/developer_onboarding.md).

### Troubleshooting

If Pylance shows unresolved imports or type errors, your editor may not be
using the virtual environment where dependencies were installed. Try the
following steps:

1. Activate the virtual environment:
   ```bash
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   ./scripts/setup.sh
   ```
   The script installs both requirement files. If you encounter errors like
   `module 'flask' has no attribute 'helpers'`,
   ensure there are no local directories named `flask`, `pandas`, or `yaml`
   in the project root. These placeholder packages can shadow the real
   libraries installed from `requirements.txt`. Delete them before running
   the application.

3. Restart your editor so Pylance picks up the correct interpreter.

4. If the dashboard starts with a blank page, required packages are
   likely missing. Install them before launching the app:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   # or simply run ./scripts/setup.sh
   ```
5. If Dash packages behave unexpectedly, reinstall them with pinned versions:
   ```bash
   pip uninstall -y dash dash-leaflet dash-extensions dash-bootstrap-components
   pip install dash==2.14.1
   pip install dash-bootstrap-components==1.6.0
   pip install dash-extensions==1.0.11
   pip install dash-leaflet==0.1.28
   pip install -r requirements.txt
   ```
6. If you accidentally open the app with `https://` instead of `http://`,
   your browser may cache a service worker or enforce HSTS, preventing the
   plain HTTP version from loading. Use the browser's development settings to
   clear site data, including service workers and caches, and remove any HSTS
   entries before reloading the page.
7. If `python app.py` fails with `NameError: name '_env_file_callback' is not defined`,
   Flask was likely installed incorrectly. Reinstall it to restore the missing
   function:
   ```bash
   pip install --force-reinstall "Flask>=2.2.5"
   ```
   See [docs/troubleshooting.md](docs/troubleshooting.md) for details.

### Production Deployment

Using Docker Compose:
```bash
docker-compose -f docker-compose.prod.yml up -d
```
Whenever you modify the code, rebuild the Docker image with `docker-compose build` (or `docker-compose up --build`) so the running container picks up your changes.
Docker Compose reads sensitive values from files under the `secrets/`
directory. Create `secrets/db_password.txt` and `secrets/secret_key.txt`
containing your database password and Flask secret key before starting the
services. The files will be mounted into `/run/secrets` automatically.

Alternatively you can launch the app with Gunicorn or uWSGI. This is the
recommended approach for any production deployment. A sample Gunicorn
configuration is provided at `gunicorn.conf.py`:
```bash
gunicorn -c gunicorn.conf.py wsgi:server
# or
uwsgi --module wsgi:server
```

When `YOSAI_ENV=production` and CSRF protection is enabled, the application
initializes the `DashCSRFPlugin` to enforce strict CSRF checks.

### Production Build

Build optimized CSS assets before deployment:
```bash
npm run build-css
```
The script reads `assets/css/main.css` and outputs both
`assets/dist/main.css` and `assets/dist/main.min.css` with a source map
`assets/dist/main.min.css.map`. Any changes under `assets/css/` won't be
reflected until you rebuild the bundle with `npm run build-css` (or
`python tools/build_css.py`). When the minified file exists, the application
loads `assets/dist/main.min.css` instead of the source CSS. Gzip or Brotli
compression is automatically handled at runtime by `flask-compress`.

## 🧪 Testing

Install dependencies before running the tests:
```bash
# Option 1: use the helper script
./scripts/setup.sh
# Option 2: install packages manually
pip install -r requirements.txt -r requirements-test.txt
```
For minimal CI environments you can run `./scripts/install_test_deps.sh` which
only installs the Python dependencies required for the tests.
Detailed instructions are provided in
[docs/test_setup.md](docs/test_setup.md).
The overall design of our test protocols and injection approach is
documented in [docs/test_architecture.md](docs/test_architecture.md).

Run the complete test suite:
```bash
# Run all unit and integration tests
pytest

# Run type checking
mypy .

# Check code quality
black . --check
flake8 .
```

The `tests/` directory contains the integration and unit tests for the
dashboard. Key entry points include `tests/test_integration.py`,
`tests/test_analytics_integration.py`, `tests/test_ai_device_generator.py` and
`tests/test_security_service.py`.

Most asynchronous tests rely on a reusable `async_runner` fixture that
executes coroutines on a dedicated event loop. If you need to run an async
function inside a test simply pass `async_runner` and call it with your
coroutine.

## 📋 Features

- **Real-time Security Monitoring**: Live access control event monitoring
- **AI-Powered Anomaly Detection**: Advanced pattern recognition
- **Interactive Analytics**: Deep dive data analysis with file uploads
- **Automatic Data Summaries**: Charts for numeric distributions and top categories
- **Modular Architecture**: Easy to maintain, test, and extend
- **Multi-page Interface**: Organized functionality across multiple pages
- **Type-Safe**: Full type annotations and validation
- **CSRF Protection Plugin**: Optional production-ready CSRF middleware for Dash
- **Machine-Learned Column Mapping**: Trainable model for smarter CSV header recognition
- **Hardened SQL Injection Prevention**: Uses `sqlparse` and `bleach` to validate queries
- **Centralized Unicode Processing**: Use `UnicodeProcessor` and related handlers
  from `core.unicode` for safe text and SQL handling.
- **Event Driven Callbacks**: Plugins react to events via the unified
  `TrulyUnifiedCallbacks` manager.
  This single interface replaces previous callback controllers.
- **Metrics & Monitoring**: `PerformanceMonitor` tracks system performance
  using `psutil`.

**Note:** The file upload and column mapping functionality relies on `pandas`.
If `pandas` is missing these pages will be disabled. Ensure you run
`pip install -r requirements.txt` and `pip install -r requirements-dev.txt` to
install all dependencies (or execute `./scripts/setup.sh`).
`PerformanceMonitor` requires `psutil` for CPU and memory metrics, and the
file processing utilities depend on `chardet` to detect text encoding.

## 🔄 Upload Workflow

The upload page now streams files directly to a background task. Progress is
reported via Server‑Sent Events at `/upload/progress/<task_id>`. Once the server
finishes processing a file it updates the `file-info-store` so analytics pages
pick up the new dataset automatically. Mobile users can collapse the queue to
free up space and the workflow adjusts for touch interactions.

## 📱 Mobile Support

The layout is responsive down to narrow phone screens. Navigation collapses into
a hamburger menu and the drag‑and‑drop region expands to full width. All touch
targets meet the 44&nbsp;px guideline and alerts reposition so they remain
readable on mobile devices.

## 🛠️ Monitoring Setup

Runtime metrics are exposed at `/metrics` for Prometheus. A sample configuration
is provided in `monitoring/prometheus.yml`. Logstash support is available via
`logging/logstash.conf`. Dashboards can be built in Grafana or Kibana using
these data sources. See [performance_monitoring.md](docs/performance_monitoring.md)
for details.

## 🔧 Configuration

This project uses **`config/config.py`** for all application settings. The
`create_config_manager()` helper builds a `ConfigManager` composed of modular
dataclasses like `AppConfig`, `DatabaseConfig` and `SecurityConfig`. It loads a
YAML file from `config/` based on `YOSAI_ENV` or `YOSAI_CONFIG_FILE`, then
applies environment variable overrides.
The underlying loading logic lives in `config/base_loader.py` as `BaseConfigLoader`.
It handles YAML `!include` expansion, JSON files and environment variable substitution. Earlier versions used separate modules
such as `app_config.py` and `simple_config.py`; these have been replaced by this
unified loader. Register the configuration with the DI container so it can be
resolved from anywhere:


```python
from core.container import Container
from config import create_config_manager

container = Container()
container.register("config", create_config_manager())

config = container.get("config")
```

A short example without the container:

```python
from config import create_config_manager

config = create_config_manager()
db_cfg = config.get_database_config()
```

### Database

Configure your database in `.env`:
```
DB_TYPE=postgresql  # or 'sqlite' or 'mock'
DB_HOST=your_db_host
DB_PORT=5432
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
```

### Application

Key configuration options:
```
DEBUG=False           # Set to False for production
HOST=0.0.0.0         # Bind to all interfaces for production
PORT=8050            # Application port
SECRET_KEY=your-key  # Change for production
```

For Gunicorn deployments, host, port and log level defaults are also
defined in `gunicorn.conf.py`.

The secret key is not included in the default YAML files. Define
`SECRET_KEY` in your environment or a `.env` file before starting the
application. The example scripts under `examples/` also rely on this
variable through the `SecretManager` helper.

When `YOSAI_ENV=production` the application will refuse to start unless both
`DB_PASSWORD` and `SECRET_KEY` are provided via environment variables or Docker
secrets.

Configuration validation runs automatically at startup and logs any missing
critical settings. The new `ConfigValidator` checks that the `app`, `database`
and `security` sections exist before the server starts.

### Environment Overrides

The `ConfigManager` returned by `create_config_manager()` loads YAML files from
`config/` and then checks for environment variables. When a variable name
matches a key used in the YAML configuration (for example `DB_HOST`, `DB_USER`,
`REDIS_HOST` or `SECRET_KEY`), its value replaces the one from the file. This
lets you adjust settings without editing the YAML files.

Example:

```bash
DB_HOST=localhost
DB_USER=postgres
REDIS_HOST=localhost
SECRET_KEY=supersecret
python app.py
```

These values override `database.host`, `database.user`, `cache.host` and
`security.secret_key` from the loaded YAML.

### Selecting a YAML File

`create_config_manager()` determines which YAML file to load by inspecting
environment variables:

- `YOSAI_ENV` – set to `development`, `staging`, `production` or `test` to
  automatically load the corresponding file under `config/`.
- `YOSAI_CONFIG_FILE` – absolute path to a custom YAML file. When set it
  overrides `YOSAI_ENV`.
- `YOSAI_APP_MODE` – set to `full`, `simple` or `json-safe` to select the
  startup mode for `create_app()` (default: `full`).

Example:

```bash
YOSAI_ENV=production python app.py
# or
YOSAI_CONFIG_FILE=/path/to/custom.yaml python app.py
YOSAI_APP_MODE=simple python app.py
```

#### Dynamic Constants

`create_config_manager()` uses the internal `DynamicConfigManager` to read
optional environment variables that fine&ndash;tune security and performance
defaults:


- `PBKDF2_ITERATIONS` – password hashing iterations
- `RATE_LIMIT_API` – number of requests allowed per window
- `RATE_LIMIT_WINDOW` – rate limit window in minutes
- `MAX_UPLOAD_MB` – maximum allowed upload size
- `DB_POOL_SIZE` – database connection pool size

### Plugins

Plugins live in the `plugins/` directory. Place any custom plugin package inside
this folder, for example `plugins/my_plugin/plugin.py` defining a
`create_plugin()` function. Enable the plugin by adding a section under
`plugins:` in `config/config.yaml` and setting `enabled: true` plus any plugin
options. Initialize plugins by calling `setup_plugins` from
`core.plugins.auto_config`. This discovers plugins, registers callbacks, exposes
`/health/plugins` and attaches the manager as `app._yosai_plugin_manager`.
See [docs/plugins.md](docs/plugins.md) for a detailed overview of discovery,
configuration and the plugin lifecycle. For step-by-step instructions on
writing your own plugin check [docs/plugin_development.md](docs/plugin_development.md).
For a diagram of the full process see [docs/plugin_lifecycle.md](docs/plugin_lifecycle.md).
The same document includes a minimal **Hello World** plugin showcasing
`create_plugin()` and callback registration.

### Migration Notes

Older modules `config/app_config.py`, `config/simple_config.py` and the
previous `config_manager.py` have been removed. Create a container and access
the new unified configuration through it instead:

```python
from core.container import Container
from config import create_config_manager

container = Container()
container.register("config", create_config_manager())

config = container.get("config")
```

The `ConfigManager` implements `ConfigurationProtocol` so alternative
implementations can be swapped in for tests. Helper functions like
`get_app_config()` and `get_database_config()` remain available for convenience.

## 🔄 Migration Guide

The dashboard now centralizes Unicode handling in `core.unicode`.
Detect legacy usage and validate the migration with the helper tools:

```bash
python tools/legacy_unicode_audit.py --path .
python tools/validate_unicode_migration.py
```

The repository also includes a helper for enforcing snake_case names.
Scan the codebase and automatically fix issues with:

```bash
python tools/naming_standardizer.py scan .
python tools/naming_standardizer.py fix <path>
```

See [docs/migration_guide.md](docs/migration_guide.md) for step-by-step
instructions and benefits of the new processors.

## 📊 Plugin Performance Monitoring

Use `EnhancedThreadSafePluginManager` to track plugin load times and
resource usage:

```python
from core.plugins.performance_manager import EnhancedThreadSafePluginManager
manager = EnhancedThreadSafePluginManager(container, config)
data = manager.get_plugin_performance_metrics()
```

The `/api/v1/plugins/performance` endpoint exposes metrics for dashboards.

## 📊 Modular Components

### Database Layer (`config/`)
- **database_manager.py**: Connection pooling, multiple database support
- Supports PostgreSQL, SQLite, and Mock databases
- Type-safe connection management
- Retry logic via `connection_retry.py` with exponential backoff
 - Safe Unicode handling using `UnicodeSQLProcessor` for queries and
   `UnicodeProcessor` for parameters
- Connection pooling through `connection_pool.py`
```python
from config.database_manager import EnhancedPostgreSQLManager, DatabaseConfig
manager = EnhancedPostgreSQLManager(DatabaseConfig(type="postgresql"))
manager.execute_query_with_retry("SELECT 1")
```

### Models Layer (`models/`)
- **entities.py**: Core business entities
- **events.py**: Event and transaction models
- **enums.py**: Type-safe enumerations
- Full type annotations and validation
- **Guide**: [docs/models_guide.md](docs/models_guide.md) explains each model file

-### Services Layer (`services/`)
- **analytics_service.py**: Business logic for analytics ([docs](docs/analytics_service.md))
  
  Register an instance with the container to access analytics operations:

  ```python
  from core.container import Container
  from services.analytics_service import create_analytics_service

  container = Container()
  container.register("analytics", create_analytics_service())

  analytics = container.get("analytics")
  ```
  
  The `AnalyticsService` conforms to `AnalyticsServiceProtocol`, so you can
  substitute your own implementation during tests.
- **device_learning_service.py**: Persists learned device mappings ([docs](docs/device_learning_service.md))
- Caching and performance optimization
- Modular and testable

### Components Layer (`components/`)
- Reusable UI components
- Independent and testable
- Type-safe prop interfaces

### SQL Injection Prevention
Use `SecurityValidator` to sanitize query parameters in both Flask and Dash routes. Example:

```python
from core.security_validator import SecurityValidator

validator = SecurityValidator()

@app.route('/search')
def search():
    term = request.args.get('q', '')
    validator.validate_input(term, 'query_parameter')
    return query_db(term)
```

### Safe JSON Serialization
`SafeJSONSerializer` in `core/serialization/safe_json.py` normalizes `LazyString`,
`Markup`, and problematic Unicode surrogate characters before any JSON encoding.
`JsonSerializationService` uses this helper to ensure consistent results across
Flask and Dash applications.

## 🔐 Authentication & Secrets

This project uses Auth0 for OIDC login. Configure the following environment
variables or Docker secrets:

- `AUTH0_CLIENT_ID`
- `AUTH0_CLIENT_SECRET`
- `AUTH0_DOMAIN`
- `AUTH0_AUDIENCE`

All secrets can be provided via the `SecretManager` which supports `env`,
`aws`, and `vault` backends. Place these values in `.env` or mount them as
Docker secrets. See the [architecture diagram](docs/auth_flow.png) for
implementation details.

Session cookies are marked as permanent on login. The default lifetime is
configured via `security.session_timeout` in seconds. You can override the
timeout for specific roles using `security.session_timeout_by_role`:

```yaml
security:
  session_timeout: 3600
  session_timeout_by_role:
    admin: 7200
    basic: 1800
```

The configuration loader performs a validation step on startup to ensure
required secrets are set. See
[docs/secret_management.md](docs/secret_management.md) for rotation
procedures, Docker/cloud secret usage, and incident handling guidance.

## 🌐 Language Toggle

Internationalization is built in with Flask-Babel. Click the language dropdown in the navigation bar to switch between English and Japanese. No additional environment variables are required.
If you encounter an error like `"Babel" object has no attribute "localeselector"` when starting the app, ensure that the `Flask-Babel` package is installed and up to date (version 4 or later). The application now falls back to the new `locale_selector_func` API when needed.
The compiled `.mo` files in `translations/` must exist at runtime. After editing any `.po` files run `pybabel compile -d translations` and commit the generated files.


## 🎨 Theme Support

The dashboard provides light, dark and high‑contrast themes. The current
selection is saved in the browser and applied before CSS loads to avoid a flash
of unstyled content. Use the new dropdown on the right side of the navbar to
switch themes at runtime.

## 📚 Documentation

See the [data model diagram](docs/data_model.md) for an overview of key entities.
The running application exposes Swagger-based API docs at `http://<host>:<port>/api/docs`.
- Performance & log monitoring: [docs/performance_monitoring.md](docs/performance_monitoring.md)
- Large file processing: [docs/performance_file_processor.md](docs/performance_file_processor.md)
- Upload progress SSE: `/upload/progress/<task_id>` streams `data: <progress>` events roughly 60 times per second.
- Callback design: [docs/callback_architecture.md](docs/callback_architecture.md)
- State stores: [docs/state_management.md](docs/state_management.md)
- Ops reference: [docs/operations_guide.md](docs/operations_guide.md)
- Callback migration: [docs/migration_callback_system.md](docs/migration_callback_system.md)

Update the spec by running `python tools/generate_openapi.py` which writes `docs/openapi.json` for the UI.
## Usage Examples

### Cleaning text
```python
from core.unicode import get_text_processor
raw = "Bad\uD83DText"
processor = get_text_processor()
clean = processor.safe_encode_text(raw)
```

### Firing events
```python
from core.callback_manager import CallbackManager
from core.callback_events import CallbackEvent

manager = CallbackManager()
manager.trigger(CallbackEvent.ANALYSIS_COMPLETE, "analytics", {"rows": 42})
```

Performance metrics can be retrieved via:
```python
from core.performance import get_performance_monitor
summary = get_performance_monitor().get_metrics_summary()
```
### Standardizing column names
```python
import pandas as pd
from utils.mapping_helpers import standardize_column_names

df = pd.DataFrame({"A B": [1], "C-D": [2]})
clean_df = standardize_column_names(df)
```
## 📜 Data Migration
Use the storage utilities to convert legacy pickle files to Parquet and load them:
```python
from file_conversion.migrate_existing_files import main
main()
```
This creates `converted_data/Demo3_data_copy.csv.parquet` and prints the first rows.

Legacy `.pkl` files placed in `temp/uploaded_data` are automatically converted
to Parquet the next time the application starts.

Uploaded files are now **lazy loaded**. Only the `file_info.json` metadata is
read at startup; Parquet files are opened on demand when analytics or previews
require them. This keeps startup fast even with many large uploads.

Uploaded data is persisted inside `temp/uploaded_data`. Each successful
upload creates a `<name>.parquet` file along with metadata in
`file_info.json`. The analytics page lists these entries in the **Data Source**
dropdown so you can revisit earlier uploads without re-uploading them.

**Important:** keep the `temp/uploaded_data` directory intact until device
mappings have been saved, otherwise the mapping step will fail.


## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines. In short:

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   pip install -r requirements-test.txt
   ```
2. Ensure all tests pass: `pytest`
3. Format code with `black` and run `flake8`
4. Follow type safety guidelines and maintain the modular architecture
5. Add tests for new functionality and update documentation when applicable
6. Optional debug helpers live in `examples/`. Run the upload helper with
   `python examples/debug_live_upload.py` to validate environment setup
7. The example CSRF scripts in `examples/` read `SECRET_KEY` from the
   environment using the `SecretManager`. Set this variable in your shell or
   `.env` file before running them.
8. A legacy `lazystring` fix plugin sample is kept in
   `examples/legacy_lazystring_fix_plugin.py` for reference only.
9. The full pipeline diagnostic helper now lives at
   `examples/diagnostic_script.py` (replacing the old
   `examples/debugcsv.py`) and can be run with
   `python examples/diagnostic_script.py`.

## 📦 Versioning

This project adheres to [Semantic Versioning](https://semver.org). See
[docs/release.md](docs/release.md) for details on how releases are managed.

## 📄 License

MIT License - see LICENSE file for details.
