import base64

import pandas as pd
import pytest

from core.callback_events import CallbackEvent
from core.callbacks import UnifiedCallbackManager as CallbackManager
from tests.utils.builders import DataFrameBuilder, UploadFileBuilder


class TemporaryCallback:
    def __init__(self, event: CallbackEvent, cb):
        self.manager = _GLOBAL_MANAGER
        self.event = event
        self.cb = cb

    def __enter__(self):
        self.manager.register_callback(self.event, self.cb)
        return self.cb

    def __exit__(self, exc_type, exc, tb):
        self.manager.unregister_callback(self.event, self.cb)


from file_conversion.storage_manager import StorageManager
from services.unified_file_controller import (
    batch_migrate_legacy_files,
)
from services.unified_file_controller import callback_manager as _GLOBAL_MANAGER
from services.unified_file_controller import (
    get_processing_metrics,
    process_file_upload,
)


def _encode_df(df: pd.DataFrame) -> str:
    return UploadFileBuilder().with_dataframe(df).as_base64()


def test_upload_workflow_and_metrics(tmp_path):
    events = []
    df = (
        DataFrameBuilder()
        .add_column("na\ud83dme", [1])
        .add_column("<script>", ["x"])
        .build()
    )
    contents = _encode_df(df)

    storage = StorageManager(base_dir=tmp_path)
    with TemporaryCallback(
        CallbackEvent.DATA_PROCESSED,
        lambda ctx: events.append(ctx.data),
    ):
        _ = process_file_upload(contents, "test.csv", storage=storage)

    loaded, err = storage.load_dataframe("test")
    assert err == ""
    assert "script" not in loaded.columns[0].lower()
    assert events and events[0]["filename"].endswith(".csv")

    metrics = get_processing_metrics()
    assert metrics["uploaded_files"] == 1
    assert metrics["total_rows"] == 1


def test_batch_migration_and_progress(tmp_path):
    df = DataFrameBuilder().add_column("a", [1]).build()
    p1 = tmp_path / "one.pkl"
    p2 = tmp_path / "two.pkl"
    df.to_pickle(p1)
    df.to_pickle(p2)

    storage = StorageManager(base_dir=tmp_path / "conv")
    progress = []
    batch_migrate_legacy_files(
        [p1, p2],
        storage=storage,
        progress=lambda i, t, n: progress.append((i, t, n)),
    )

    assert (tmp_path / "conv" / "one.parquet").exists()
    assert (tmp_path / "conv" / "two.parquet").exists()
    assert progress == [(1, 2, "one.pkl"), (2, 2, "two.pkl")]

    metrics = get_processing_metrics()
    assert metrics["migrated_files"] == 2


def test_batch_migration_handles_unicode_names(tmp_path):
    df = DataFrameBuilder().add_column("a", [1]).build()
    emoji = tmp_path / "\U0001f600.pkl"
    df.to_pickle(emoji)

    storage = StorageManager(base_dir=tmp_path / "uni")
    calls = []
    batch_migrate_legacy_files(
        [emoji], storage=storage, progress=lambda i, t, n: calls.append((i, t, n))
    )

    assert (tmp_path / "uni" / "\U0001f600.parquet").exists()
    assert calls == [(1, 1, f"{emoji.name}")]


def test_security_validation_blocks_bad_file(tmp_path):
    bad_df = DataFrameBuilder().add_column("=cmd", ["=1"]).build()
    contents = _encode_df(bad_df)
    storage = StorageManager(base_dir=tmp_path)
    with pytest.raises(Exception):
        process_file_upload(contents, "bad.csv", storage=storage)
