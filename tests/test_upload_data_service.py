import sys
import types
from tests.import_helpers import safe_import, import_optional

safe_import('flask_caching', types.SimpleNamespace(Cache=object))
if "dask" not in sys.modules:
    dask_stub = types.ModuleType("dask")
    dask_stub.__path__ = []
    dist_stub = types.ModuleType("dask.distributed")
    dist_stub.Client = object
    dist_stub.LocalCluster = object
    safe_import('dask', dask_stub)
    safe_import('dask.distributed', dist_stub)
if "dash" not in sys.modules:
    dash_stub = types.ModuleType("dash")
    safe_import('dash', dash_stub)
    safe_import('dash.dash', dash_stub)
    safe_import('dash.html', types.ModuleType("dash.html"))
    safe_import('dash.dcc', types.ModuleType("dash.dcc"))
    safe_import('dash.dependencies', types.ModuleType("dash.dependencies"))
    safe_import('dash._callback', types.ModuleType("dash._callback"))
if "chardet" not in sys.modules:
    safe_import('chardet', types.ModuleType("chardet"))
from unittest.mock import MagicMock

import pandas as pd

from yosai_intel_dashboard.src.services.upload_data_service import UploadDataService
from yosai_intel_dashboard.src.utils.upload_store import UploadedDataStore


def test_store_and_retrieve(tmp_path):
    store = UploadedDataStore(storage_dir=tmp_path)
    service = UploadDataService(store)
    df = pd.DataFrame({"a": [1, 2]})
    store.add_file("a.csv", df)
    data = service.get_uploaded_data()
    assert list(data.keys()) == ["a.csv"]
    pd.testing.assert_frame_equal(data["a.csv"], df)


def test_methods_proxy_to_store():
    mock_store = MagicMock(spec=UploadedDataStore)
    service = UploadDataService(mock_store)
    service.get_uploaded_filenames()
    service.clear_uploaded_data()
    service.load_dataframe("file.csv")
    mock_store.get_filenames.assert_called_once()
    mock_store.clear_all.assert_called_once()
    mock_store.load_dataframe.assert_called_once_with("file.csv")
