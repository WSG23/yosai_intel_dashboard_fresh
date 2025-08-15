import json

import pandas as pd

from yosai_intel_dashboard.src.services.data_processing.common import process_dataframe


def test_process_dataframe_csv_with_surrogate(tmp_path):
    csv_path = tmp_path / "bad.csv"
    text = "col1,col2\nvalue1,\ud83d\nvalue2,ok\n"
    csv_path.write_text(text, encoding="utf-8", errors="surrogatepass")
    data = csv_path.read_bytes()
    df, err = process_dataframe(data, "bad.csv")
    assert err is None
    assert isinstance(df, pd.DataFrame)
    assert df.loc[0, "col2"] == ""


def test_process_dataframe_json_with_surrogate(tmp_path):
    json_path = tmp_path / "bad.json"
    content = json.dumps({"value": "\ud83d"})
    json_path.write_text(content, encoding="utf-8", errors="surrogatepass")
    data = json_path.read_bytes()
    df, err = process_dataframe(data, "bad.json")
    assert err is None
    assert isinstance(df, pd.DataFrame)
    assert df.loc[0, "value"] == ""


def test_process_dataframe_csv_with_malformed_pairs(tmp_path):
    csv_path = tmp_path / "mal.csv"
    # High surrogate followed by normal char and lone low surrogate
    text = "col\n\ud83dX\ude0a"
    csv_path.write_text(text, encoding="utf-8", errors="surrogatepass")
    data = csv_path.read_bytes()
    df, err = process_dataframe(data, "mal.csv")
    assert err is None
    assert isinstance(df, pd.DataFrame)
    # Both invalid sequences should be dropped
    assert df.loc[0, "col"] == "X"


def test_process_dataframe_json_with_malformed_pairs(tmp_path):
    json_path = tmp_path / "mal.json"
    obj = {"v": "\ud83dX\ude0a"}
    content = json.dumps(obj)
    json_path.write_text(content, encoding="utf-8", errors="surrogatepass")
    data = json_path.read_bytes()
    df, err = process_dataframe(data, "mal.json")
    assert err is None
    assert isinstance(df, pd.DataFrame)
    assert df.loc[0, "v"] == "X"
