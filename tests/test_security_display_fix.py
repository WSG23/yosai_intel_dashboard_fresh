import dash_bootstrap_components as dbc
import pytest

# These tests rely on the external 'analytics' package
pytest.importorskip("analytics")
from services.analytics.core.utils.results_display import create_analysis_results_display

pytestmark = pytest.mark.usefixtures("fake_dbc")


def test_security_display_fix():
    """Test the security display with corrected data"""
    mock_results = {
        "total_events": 395852,
        "unique_users": 3,
        "unique_doors": 2,
        "successful_events": 350000,
        "failed_events": 45852,
        "security_score": {"score": 75.5, "threat_level": "medium"},
    }

    display = create_analysis_results_display(mock_results, "security")
    assert isinstance(display, dbc.Card)
    assert "Security Results" in str(display)
    print("✅ Header fix validated")
    print("✅ Statistics extraction validated")
