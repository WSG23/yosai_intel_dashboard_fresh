import pandas as pd
from services.analytics_service import AnalyticsService





def test_direct_processing_helper(tmp_path):
    df1 = pd.DataFrame(
        {
            "Timestamp": ["2024-01-01 10:00:00"],
            "Person ID": ["u1"],
            "Token ID": ["t1"],
            "Device name": ["d1"],
            "Access result": ["Granted"],
        }
    )
    path = tmp_path / "f1.csv"
    df1.to_csv(path, index=False)
    service = AnalyticsService()
    result = service._process_uploaded_data_directly({"f1.csv": path})
    assert result["total_events"] == 1
    assert result["active_users"] == 1
    assert result["active_doors"] == 1
