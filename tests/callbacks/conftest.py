import sys
import types
from pathlib import Path

import pytest
from tests.import_helpers import safe_import, import_optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    import dash
except ModuleNotFoundError:
    dash = types.SimpleNamespace(no_update=None)
    safe_import('dash', lambda: dash)

# Provide dash.exceptions.PreventUpdate when dash isn't installed
if "dash.exceptions" not in sys.modules:
    safe_import('dash.exceptions', lambda: types.SimpleNamespace(PreventUpdate=Exception))

# Ensure dash.no_update is defined for tests
if not hasattr(dash, "no_update"):
    # Stub sentinel or None is fine
    dash.no_update = None


@pytest.fixture(autouse=True)
def ensure_no_update():
    """Fixture to guarantee dash.no_update is present in all tests."""
    return None
