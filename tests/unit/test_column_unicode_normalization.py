import unicodedata

import pandas as pd
import importlib.util
from pathlib import Path
import sys
import types

sys.modules.setdefault(
    "yosai_intel_dashboard.src.services.analytics_summary",
    types.SimpleNamespace(summarize_dataframe=lambda df: {}),
)
sys.modules.setdefault(
    "yosai_intel_dashboard.src.services.chunked_analysis",
    types.SimpleNamespace(analyze_with_chunking=lambda df, validator, tasks: {}),
)
sys.modules.setdefault(
    "yosai_intel_dashboard.src.services.upload.protocols",
    types.SimpleNamespace(UploadAnalyticsProtocol=object),
)
sys.modules.setdefault(
    "yosai_intel_dashboard.src.utils.upload_store",
    types.SimpleNamespace(get_uploaded_data_store=lambda: types.SimpleNamespace(get_all_data=lambda: {})),
)
sys.modules.setdefault(
    "validation.data_validator",
    types.SimpleNamespace(DataValidator=object, DataValidatorProtocol=object),
)

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
upload_analytics = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = upload_analytics
spec.loader.exec_module(upload_analytics)
UploadAnalyticsProcessor = upload_analytics.UploadAnalyticsProcessor


def test_clean_uploaded_dataframe_normalizes_mixed_encoding_columns() -> None:
    df = pd.DataFrame(
        [["d1", "2024-01-01 00:00:00", 1, 2]],
        columns=["Device\u00A0name", "Event\u00A0time", "Caf\u00E9", "Cafe\u0301"],
    )
    ua = UploadAnalyticsProcessor.__new__(UploadAnalyticsProcessor)
    cleaned = UploadAnalyticsProcessor.clean_uploaded_dataframe(ua, df)

    assert "door_id" in cleaned.columns
    assert "timestamp" in cleaned.columns
    assert cleaned.columns[-2:] == ["café", "café"]
    assert all(unicodedata.is_normalized("NFKC", c) for c in cleaned.columns)
