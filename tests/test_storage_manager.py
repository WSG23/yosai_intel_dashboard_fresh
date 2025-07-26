import json
from datetime import datetime

import pandas as pd

from core.callback_events import CallbackEvent
from core.callbacks import UnifiedCallbackManager as CallbackManager


class TemporaryCallback:
    def __init__(self, event: CallbackEvent, cb, manager: CallbackManager) -> None:
        self.event = event
        self.cb = cb
        self.manager = manager

    def __enter__(self):
        self.manager.register_callback(self.event, self.cb)
        return self.cb

    def __exit__(self, exc_type, exc, tb):
        self.manager.unregister_callback(self.event, self.cb)


from file_conversion.storage_manager import StorageManager


def test_migrate_pkl_to_parquet(tmp_path):
    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    pkl_path = tmp_path / "sample.pkl"
    df.to_pickle(pkl_path)

    controller = CallbackManager()
    controller._callbacks.clear()
    events = []

    def record(ctx):
        events.append(ctx.event_type)

    with TemporaryCallback(
        CallbackEvent.FILE_PROCESSING_START,
        record,
        controller,
    ), TemporaryCallback(
        CallbackEvent.FILE_PROCESSING_COMPLETE,
        record,
        controller,
    ), TemporaryCallback(
        CallbackEvent.FILE_PROCESSING_ERROR,
        record,
        controller,
    ):
        storage = StorageManager(base_dir=tmp_path / "converted")
        success, msg = storage.migrate_pkl_to_parquet(pkl_path)
    assert success, msg

    assert events[0] == CallbackEvent.FILE_PROCESSING_START
    assert CallbackEvent.FILE_PROCESSING_COMPLETE in events

    parquet_path = storage.base_dir / "sample.parquet"
    assert parquet_path.exists()
    loaded = pd.read_parquet(parquet_path)
    pd.testing.assert_frame_equal(loaded, df)

    metadata_path = storage.base_dir / "metadata.json"
    assert metadata_path.exists()
    metadata = json.loads(metadata_path.read_text())
    assert "sample.parquet" in metadata
    entry = metadata["sample.parquet"]
    assert entry["original_file"] == str(pkl_path)
    assert entry["rows"] == len(df)
    assert entry["columns"] == len(df.columns)
    assert "converted_at" in entry
    # ensure ISO format timestamp
    datetime.fromisoformat(entry["converted_at"])
