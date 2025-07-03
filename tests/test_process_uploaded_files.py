import base64
import pandas as pd

from pages.file_upload import Callbacks, _uploaded_data_store
from services.upload import UploadProcessingService


def test_multi_part_upload_row_count():
    df = pd.DataFrame({
        "A": [1, 2, 3, 4],
        "B": ["a", "b", "c", "d"],
    })
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    prefix = "data:text/csv;base64,"
    mid = len(b64) // 2
    part1 = prefix + b64[:mid]
    part2 = prefix + b64[mid:]

    cb = Callbacks()
    cb.processing = UploadProcessingService(_uploaded_data_store)
    res = cb.process_uploaded_files([part1, part2], ["sample.csv", "sample.csv"])
    info = res[2]
    assert info["sample.csv"]["rows"] == len(df)
    stored = _uploaded_data_store.get_all_data()["sample.csv"]
    assert len(stored) == len(df)
