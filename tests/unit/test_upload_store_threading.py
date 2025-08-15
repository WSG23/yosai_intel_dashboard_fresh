from concurrent.futures import ThreadPoolExecutor

import pandas as pd

from tests.utils.builders import DataFrameBuilder
from yosai_intel_dashboard.src.utils.upload_store import UploadedDataStore


def test_concurrent_add_file(tmp_path):
    store = UploadedDataStore(storage_dir=tmp_path)

    def worker(i: int) -> None:
        df = DataFrameBuilder().add_column("val", [i]).build()
        store.add_file(f"file_{i}.csv", df)

    with ThreadPoolExecutor(max_workers=5) as exc:
        list(exc.map(worker, range(10)))

    store.wait_for_pending_saves()

    assert set(store.get_filenames()) == {f"file_{i}.csv" for i in range(10)}
    data = store.get_all_data()
    for i in range(10):
        pd.testing.assert_frame_equal(
            data[f"file_{i}.csv"], DataFrameBuilder().add_column("val", [i]).build()
        )

    # verify files persisted to disk and can be reloaded
    parquet_files = list(tmp_path.glob("*.parquet"))
    assert len(parquet_files) == 10
    reloaded = UploadedDataStore(storage_dir=tmp_path)
    assert set(reloaded.get_filenames()) == {f"file_{i}.csv" for i in range(10)}
    for i in range(10):
        pd.testing.assert_frame_equal(
            reloaded.get_all_data()[f"file_{i}.csv"],
            DataFrameBuilder().add_column("val", [i]).build(),
        )
