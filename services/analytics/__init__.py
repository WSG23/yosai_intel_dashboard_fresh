import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def analyze_uploaded_data(uploaded_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Return analytics for uploaded files.

    When ``uploaded_data`` is provided it should be a mapping of filename to
    source (either a dataframe or path).  Otherwise data will be loaded from the
    persistent upload store.
    """
    from services.analytics_service import AnalyticsService

    service = AnalyticsService()
    if uploaded_data is not None:
        return service._process_uploaded_data_directly(uploaded_data)
    return service._get_real_uploaded_data()


__all__ = ["analyze_uploaded_data"]
