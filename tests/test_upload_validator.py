import base64
from pathlib import Path

import pandas as pd

from upload_validator import UploadValidator


def test_validate_file_upload_dataframe():
    df = pd.DataFrame({"a": [1]})
    v = UploadValidator(max_size_mb=1)
    res = v.validate_file_upload(df)
    assert res.valid


def test_validate_file_upload_base64(tmp_path):
    data = b"a,b\n1,2\n"
    b64 = base64.b64encode(data).decode()
    uri = "data:text/csv;base64," + b64
    v = UploadValidator(max_size_mb=1)
    res = v.validate_file_upload(uri)
    assert res.valid


def test_validate_file_upload_path(tmp_path):
    path = tmp_path / "file.csv"
    path.write_text("a,b\n1,2\n")
    v = UploadValidator(max_size_mb=1)
    res = v.validate_file_upload(path)
    assert res.valid
