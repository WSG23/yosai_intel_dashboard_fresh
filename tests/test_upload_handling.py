import pandas as pd
from pages.file_upload.upload_handling import (
    build_success_alert,
    build_failure_alert,
    build_file_preview_component,
)


def test_build_success_alert_basic():
    alert = build_success_alert("test.csv", 10, 2)
    assert "test.csv" in alert.children[0].children[1]


def test_build_failure_alert():
    alert = build_failure_alert("oops")
    assert "oops" in alert.children[1].children


def test_build_file_preview_component():
    df = pd.DataFrame({"a": [1, 2]})
    comp = build_file_preview_component(df, "a.csv")
    assert any("Data Configuration" in c.children for c in comp.children if hasattr(c, "children"))
