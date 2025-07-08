from pathlib import Path
import sys
import shutil

from tests.utils.builders import DataFrameBuilder, UploadFileBuilder

# Ensure the real Dash package is used even if test stubs are on sys.path
stub_dir = Path(__file__).resolve().parent / "stubs"
if str(stub_dir) in sys.path:
    sys.path.remove(str(stub_dir))

import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
import pytest

if str(stub_dir) not in sys.path:
    sys.path.insert(0, str(stub_dir))

from core.truly_unified_callbacks import TrulyUnifiedCallbacks
from pages import file_upload
from components.upload import UnifiedUploadComponent
from core.unicode import safe_unicode_encode


@pytest.fixture
def _skip_if_no_chromedriver() -> None:
    if not shutil.which("chromedriver"):
        pytest.skip("chromedriver not installed")


def create_sample_files(tmp_path: Path) -> dict[str, Path]:
    df = DataFrameBuilder().add_column("col", ["hello", "😀"]).build()
    csv = UploadFileBuilder().with_dataframe(df).write_csv(tmp_path / "sample.csv")
    df.to_excel(tmp_path / "sample.xlsx", index=False)
    df.to_json(tmp_path / "sample.json", force_ascii=False, orient="records")
    excel = tmp_path / "sample.xlsx"
    jsonf = tmp_path / "sample.json"
    return {"csv": csv, "excel": excel, "json": jsonf}


def _create_app() -> dash.Dash:
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    coord = TrulyUnifiedCallbacks(app)
    file_upload.register_upload_callbacks(coord)
    app.layout = html.Div([dcc.Location(id="url"), file_upload.layout()])
    return app


def test_file_upload_component_integration(_skip_if_no_chromedriver, dash_duo, tmp_path):

    files = create_sample_files(tmp_path)
    app = _create_app()
    dash_duo.start_server(app)

    file_input = dash_duo.find_element("#drag-drop-upload input")
    to_send = "\n".join(str(p) for p in files.values())
    file_input.send_keys(to_send)

    dash_duo.wait_for_text_to_contain("#upload-results", "Successfully uploaded", timeout=10)
    dash_duo.wait_for_text_to_equal("#upload-progress", "100%", timeout=10)

    uploaded = file_upload.get_uploaded_filenames()
    assert sorted(uploaded) == sorted(p.name for p in files.values())
    assert isinstance(file_upload._upload_component, UnifiedUploadComponent)


def test_safe_unicode_encode_edge_cases():
    bytes_val = "X".encode("utf-8") + "\ud83d".encode("utf-8", "surrogatepass")
    assert safe_unicode_encode(bytes_val) == "X"
    assert safe_unicode_encode("A" + chr(0xD800) + "B") == "AB"
    assert safe_unicode_encode(None) == ""
