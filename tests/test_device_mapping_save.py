import asyncio
import base64

import pytest
import dash_bootstrap_components as dbc
import pandas as pd

from services.upload import UploadProcessingService
from upload_core import UploadCore
from utils.upload_store import UploadedDataStore
from services.device_learning_service import DeviceLearningService
from tests.fakes import FakeUploadDataService

pytestmark = pytest.mark.usefixtures("fake_dbc")


def _encode_df(df: pd.DataFrame) -> str:
    data = df.to_csv(index=False).encode()
    b64 = base64.b64encode(data).decode()
    return f"data:text/csv;base64,{b64}"


def test_immediate_confirm_after_upload(monkeypatch, tmp_path, async_runner):
    import importlib
    import pages
    from tests.fakes import FakeGraphs

    fake_graphs = FakeGraphs()
    monkeypatch.setattr(pages, "graphs", fake_graphs, raising=False)
    if hasattr(pages, "_pages"):
        monkeypatch.setitem(pages._pages, "graphs", fake_graphs)

    file_upload = importlib.import_module("pages.file_upload")
    Callbacks = UploadCore

    store = UploadedDataStore(storage_dir=tmp_path)
    monkeypatch.setattr(file_upload, "_uploaded_data_store", store)

    learning = DeviceLearningService()
    data_svc = FakeUploadDataService(store)
    processing = UploadProcessingService(store, learning, data_svc)
    cb = Callbacks(processing, learning, store)
    ok, msg = cb.validator.validate("data.csv", _encode_df(pd.DataFrame()))
    assert ok, msg

    df = pd.DataFrame({"device": ["Door1"], "val": [1]})
    content = _encode_df(df)

    # Simulate upload which triggers async disk save
    async_runner(cb.process_uploaded_files(content, "data.csv"))

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
