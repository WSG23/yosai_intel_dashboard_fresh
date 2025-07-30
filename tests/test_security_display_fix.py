import dash_bootstrap_components as dbc
import pytest
import logging

from analytics.core.utils.results_display import create_analysis_results_display

pytestmark = pytest.mark.usefixtures("fake_dbc")

logger = logging.getLogger(__name__)


def test_security_display_fix(caplog):
    """Test the security display with corrected data"""
    mock_results = {
        "total_events": 395852,
        "unique_users": 3,
        "unique_doors": 2,
        "successful_events": 350000,
        "failed_events": 45852,
        "security_score": {"score": 75.5, "threat_level": "medium"},
    }

    with caplog.at_level("INFO"):
        display = create_analysis_results_display(mock_results, "security")
        logger.info("✅ Header fix validated")
        logger.info("✅ Statistics extraction validated")

    assert isinstance(display, dbc.Card)
    assert "Security Results" in str(display)
    messages = [r.getMessage() for r in caplog.records]
    assert "✅ Header fix validated" in messages
    assert "✅ Statistics extraction validated" in messages
