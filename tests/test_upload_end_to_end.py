import time
import sys
from pathlib import Path
import pandas as pd
from tests.utils.builders import DataFrameBuilder, UploadFileBuilder

import services.upload as su
from services.upload.core.validator import ClientSideValidator
from services.upload.modal import ModalService
from services.upload.helpers import get_trigger_id


class StubChunkedUploadManager:
    def __init__(self, *_, **__):
        self._progress = 0

    def start_file(self, _):
        self._progress = 0

    def finish_file(self, _):
        self._progress = 100

    def get_progress(self, _):
        return self._progress


if not hasattr(su, "AISuggestionService"):
    su.AISuggestionService = type("AISuggestionService", (), {})
    su.ChunkedUploadManager = StubChunkedUploadManager
    su.ClientSideValidator = ClientSideValidator
    su.ModalService = ModalService
    su.get_trigger_id = get_trigger_id


class FakeUploadStore:
    def __init__(self) -> None:
        self.data: dict[str, pd.DataFrame] = {}

    def add_file(self, filename: str, dataframe: pd.DataFrame) -> None:
        self.data[filename] = dataframe

    def get_all_data(self) -> dict[str, pd.DataFrame]:
        return self.data.copy()

    def clear_all(self) -> None:
        self.data.clear()

    def load_dataframe(self, filename: str) -> pd.DataFrame | None:
        return self.data.get(filename)

    def get_filenames(self) -> list[str]:
        return list(self.data.keys())

    def get_file_info(self) -> dict[str, dict[str, int]]:
        return {
            name: {"rows": len(df), "columns": len(df.columns)}
            for name, df in self.data.items()
        }

    def wait_for_pending_saves(self) -> None:
        pass


class FakeUploadDataService:
    def __init__(self, store: FakeUploadStore) -> None:
        self.store = store

    def get_uploaded_data(self) -> dict[str, pd.DataFrame]:
        return self.store.get_all_data()

    def get_uploaded_filenames(self) -> list[str]:
        return self.store.get_filenames()

    def clear_uploaded_data(self) -> None:
        self.store.clear_all()

    def get_file_info(self) -> dict[str, dict[str, int]]:
        return self.store.get_file_info()

    def load_dataframe(self, filename: str) -> pd.DataFrame:
        df = self.store.load_dataframe(filename)
        if df is None:
            raise FileNotFoundError(filename)
        return df


class FakeDeviceLearningService:
    def __init__(self) -> None:
        self.saved: dict[str, dict[str, int]] = {}

    def get_learned_mappings(self, df: pd.DataFrame, filename: str) -> dict[str, dict]:
        return {}

    def apply_learned_mappings_to_global_store(
        self, df: pd.DataFrame, filename: str
    ) -> bool:
        return False

    def get_user_device_mappings(self, filename: str) -> dict[str, int]:
        return self.saved.get(filename, {})

    def save_user_device_mappings(
        self, df: pd.DataFrame, filename: str, user_mappings: dict[str, int]
    ) -> bool:
        self.saved[filename] = user_mappings
        return True


class FakeFileProcessor:
    async def process_file(
        self, content: str, filename: str, progress_callback=None
    ) -> pd.DataFrame:
        import base64
        from io import BytesIO

        _, data = content.split(",", 1)
        raw = base64.b64decode(data)
        df = (
            pd.read_csv(BytesIO(raw))
            if filename.lower().endswith(".csv")
            else pd.DataFrame()
        )
        if progress_callback:
            try:
                progress_callback(filename, 100)
            except Exception:
                pass
        return df

    def read_uploaded_file(
        self, contents: str, filename: str
    ) -> tuple[pd.DataFrame, str]:
        import base64
        from io import BytesIO

        _, data = contents.split(",", 1)
        raw = base64.b64decode(data)
        df = (
            pd.read_csv(BytesIO(raw))
            if filename.lower().endswith(".csv")
            else pd.DataFrame()
        )
        return df, ""


from services.upload.core.processor import UploadProcessingService
from upload_core import UploadCore
from core.truly_unified_callbacks import TrulyUnifiedCallbacks
from core.callback_registry import _callback_registry
from pages import file_upload
from dash import Dash


def test_complete_upload_flow(tmp_path):
    df = DataFrameBuilder().add_column("a", range(5)).build()
    content = UploadFileBuilder().with_dataframe(df).as_base64()

    store = FakeUploadStore()
    learning = FakeDeviceLearningService()
    data_svc = FakeUploadDataService(store)
    processing = UploadProcessingService(
        store, learning, data_svc, processor=FakeFileProcessor()
    )
    core = UploadCore(processing, learning, store)

    tid = core.schedule_upload_task(content, "sample.csv")

    progress = 0
    for _ in range(200):
        progress, _pct, _items = core.update_progress_bar(0, tid)
        if progress >= 100:
            break
        time.sleep(0.01)

    assert progress == 100

    result = core.finalize_upload_results(1, tid)
    assert result[-1] is True

    saved = store.load_dataframe("sample.csv")
    pd.testing.assert_frame_equal(saved, df)


def test_callback_connectivity(fake_dash):
    app = Dash()
    coord = TrulyUnifiedCallbacks(app)

    _callback_registry.registered_callbacks.clear()
    _callback_registry.registration_sources.clear()
    _callback_registry.registration_order.clear()
    _callback_registry.registration_attempts.clear()

    comp = file_upload.load_page()
    comp.register_callbacks(coord)

    expected = {
        "file_upload_handle",
        "file_upload_progress",
        "file_upload_finalize",
    }
    assert expected.issubset(_callback_registry.registered_callbacks)
    first = len(_callback_registry.registered_callbacks)

    comp.register_callbacks(coord)
    assert len(_callback_registry.registered_callbacks) == first
