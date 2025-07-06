import base64

import pandas as pd

from services.data_processing.file_processor import FileProcessor


def test_read_uploaded_file_basic():
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    encoded = base64.b64encode(df.to_csv(index=False).encode()).decode()
    contents = f"data:text/csv;base64,{encoded}"
    processor = FileProcessor()
    loaded, size = processor.read_uploaded_file(contents, "sample.csv")
    assert len(loaded) == len(df)
    assert size > 0
