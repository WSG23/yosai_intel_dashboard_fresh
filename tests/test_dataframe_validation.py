import importlib.util
import sys
import types
from pathlib import Path

import pandas as pd
import pytest

# Stub dependencies required by upload_analytics during import
sys.modules.setdefault(
    "yosai_intel_dashboard.src.services.analytics_summary",
    types.SimpleNamespace(summarize_dataframe=lambda df: {"rows": len(df)})
)
sys.modules.setdefault(
    "yosai_intel_dashboard.src.services.chunked_analysis",
    types.SimpleNamespace(analyze_with_chunking=lambda df, v, t: {})
)
sys.modules.setdefault(
    "yosai_intel_dashboard.src.services.upload.protocols",
    types.SimpleNamespace(UploadAnalyticsProtocol=object)
)
sys.modules.setdefault(
    "yosai_intel_dashboard.src.utils.upload_store",
    types.SimpleNamespace(get_uploaded_data_store=lambda: types.SimpleNamespace(get_all_data=lambda: {}))
)
sys.modules.setdefault(
    "validation.data_validator",
    types.SimpleNamespace(DataValidator=object, DataValidatorProtocol=object)
)

# Ensure real pandas is used
sys.modules.pop("pandas", None)
import pandas as pd  # reload real pandas

base = Path("yosai_intel_dashboard/src").resolve()
pkg_paths = {
    "yosai_intel_dashboard": Path("yosai_intel_dashboard").resolve(),
    "yosai_intel_dashboard.src": base,
    "yosai_intel_dashboard.src.services": base / "services",
    "yosai_intel_dashboard.src.services.analytics": base / "services" / "analytics",
}
for name, path in pkg_paths.items():
    module = sys.modules.setdefault(name, types.ModuleType(name))
    module.__path__ = [str(path)]

spec = importlib.util.spec_from_file_location(
    "yosai_intel_dashboard.src.services.analytics.upload_analytics",
    Path("yosai_intel_dashboard/src/services/analytics/upload_analytics.py"),
)
ua = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = ua
assert spec.loader is not None
spec.loader.exec_module(ua)


def test_summarize_dataframes_requires_columns():
    df = pd.DataFrame({"timestamp": pd.to_datetime(["2024-01-01"])})
    with pytest.raises(ValueError) as exc:
        ua.summarize_dataframes([df])
    assert "events" in str(exc.value)


def test_summarize_dataframes_validates_timestamp():
    df = pd.DataFrame({"events": [1]})
    with pytest.raises(ValueError) as exc:
        ua.summarize_dataframes([df])
    assert "timestamp" in str(exc.value)


def test_summarize_dataframes_success():
    df = pd.DataFrame({"timestamp": pd.date_range("2024-01-01", periods=2), "events": [1, 2]})
    summary = ua.summarize_dataframes([df])
    assert summary["status"] == "success"
    assert summary["files_processed"] == 1
