import pytest
import dash

# Ensure dash.no_update is defined for tests
if not hasattr(dash, "no_update"):
    # Stub sentinel or None is fine
    dash.no_update = None

@pytest.fixture(autouse=True)
def ensure_no_update():
    """Fixture to guarantee dash.no_update is present in all tests."""
    return None
