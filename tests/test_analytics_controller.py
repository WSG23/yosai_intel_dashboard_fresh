import pandas as pd

from analytics.business_service import AnalyticsBusinessService
from analytics.data_repository import AnalyticsDataRepository
from analytics.ui_controller import AnalyticsUIController
from core.callback_events import CallbackEvent
from core.callbacks import UnifiedCallbackManager as CallbackManager


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "person_id": ["u1", "u2"],
            "door_id": ["d1", "d2"],
            "access_result": ["Granted", "Denied"],
        }
    )


def test_business_service_analysis():
    repo = AnalyticsDataRepository()
    service = AnalyticsBusinessService(repo)
    df = _sample_df()
    results = service.run_analysis(df)
    assert results["total_events"] == 2
    assert results["unique_users"] == 2
    assert results["unique_doors"] == 2


def test_ui_controller_callbacks():
    repo = AnalyticsDataRepository()
    service = AnalyticsBusinessService(repo)
    callback_manager = CallbackManager()
    ui = AnalyticsUIController(service, callback_manager)

    events: list[str] = []
    callback_manager.register_callback(
        CallbackEvent.ANALYSIS_START, lambda ctx: events.append("start")
    )
    callback_manager.register_callback(
        CallbackEvent.ANALYSIS_COMPLETE, lambda ctx: events.append("complete")
    )

    df = _sample_df()
    results = ui.handle_analysis_request(df)

    assert results["total_events"] == 2
    assert events == ["start", "complete"]
