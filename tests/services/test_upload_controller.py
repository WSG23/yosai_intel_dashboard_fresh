import base64
import json

from yosai_intel_dashboard.src.services.upload.controllers.upload_controller import (
    UnifiedUploadController,
)


def test_parse_upload_csv_handles_surrogates():
    controller = UnifiedUploadController()
    csv = "col\n\udce2"
    contents = (
        "data:text/csv;base64," + base64.b64encode(csv.encode("utf-8", "surrogatepass")).decode()
    )
    df = controller.parse_upload(contents, "sample.csv")
    assert df is not None
    assert df.iloc[0, 0] == ""


def test_parse_upload_json():
    controller = UnifiedUploadController()
    data = [{"a": 1}, {"a": 2}]
    json_text = json.dumps(data)
    contents = (
        "data:application/json;base64," + base64.b64encode(json_text.encode("utf-8")).decode()
    )
    df = controller.parse_upload(contents, "data.json")
    assert list(df["a"]) == [1, 2]
