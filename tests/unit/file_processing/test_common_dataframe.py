import pandas as pd

from yosai_intel_dashboard.src.services.data_processing.common import process_dataframe


def test_process_dataframe_csv(tmp_path):
    df = pd.DataFrame({"a": [1, 2]})
    path = tmp_path / "data.csv"
    df.to_csv(path, index=False)

    data = path.read_bytes()
    out, err = process_dataframe(data, "data.csv")

    assert err is None
    pd.testing.assert_frame_equal(out, df.astype(str))


def test_process_dataframe_bad_extension():
    data = b"text"
    df, err = process_dataframe(data, "bad.txt")
    assert df is None
    assert "Unsupported file type" in err
