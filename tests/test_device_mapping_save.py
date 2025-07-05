import base64
import pandas as pd
import dash_bootstrap_components as dbc
import asyncio
from services.upload import UploadProcessingService
from utils.upload_store import UploadedDataStore


def _encode_df(df: pd.DataFrame) -> str:
    data = df.to_csv(index=False).encode()
    b64 = base64.b64encode(data).decode()
    return f"data:text/csv;base64,{b64}"


def test_immediate_confirm_after_upload(monkeypatch, tmp_path):
    import importlib
    import sys
    import types

    sys.modules["pages.graphs"] = types.ModuleType("pages.graphs")
    sys.modules["pages.graphs"].GRAPH_FIGURES = {}

    utils_module = importlib.import_module("pages.upload_utils")
    Callbacks = importlib.import_module("pages.upload_callbacks").Callbacks

    store = UploadedDataStore(storage_dir=tmp_path)
    monkeypatch.setattr(utils_module, "_uploaded_data_store", store)

    cb = Callbacks()
    cb.processing = UploadProcessingService(store)

    df = pd.DataFrame({"device": ["Door1"], "val": [1]})
    content = _encode_df(df)

    # Simulate upload which triggers async disk save
    asyncio.run(cb.process_uploaded_files(content, "data.csv"))

    file_info = {"filename": "data.csv", "devices": ["Door1"]}
    alert, _, _ = cb.save_confirmed_device_mappings(
        1,
        [1],
        [5],
        [[]],
        [[]],
        file_info,
    )

    assert isinstance(alert, dbc.Toast)
    assert "cannot save mappings" not in alert.children
