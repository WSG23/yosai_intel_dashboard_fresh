import json
import pandas as pd
from utils.file_validator import process_dataframe


def test_process_dataframe_csv_with_surrogate(tmp_path):
    csv_path = tmp_path / "bad.csv"
    text = "col1,col2\nvalue1,\ud83d\nvalue2,ok\n"
    csv_path.write_text(text, encoding="utf-8", errors="surrogatepass")
    data = csv_path.read_bytes()
    df, err = process_dataframe(data, "bad.csv")
    assert err is None
    assert isinstance(df, pd.DataFrame)
    assert df.loc[0, "col2"] == "\ud83d"


def test_process_dataframe_json_with_surrogate(tmp_path):
    json_path = tmp_path / "bad.json"
    content = json.dumps({"value": "\ud83d"})
    json_path.write_text(content, encoding="utf-8", errors="surrogatepass")
    data = json_path.read_bytes()
    df, err = process_dataframe(data, "bad.json")
    assert err is None
    assert isinstance(df, pd.DataFrame)
    assert df.loc[0, "value"] == "\ud83d"
