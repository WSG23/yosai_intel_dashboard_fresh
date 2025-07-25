from __future__ import annotations

import html
import json
from pathlib import Path
from tempfile import NamedTemporaryFile

import pandas as pd
from flask import (
    Flask,
    Response,
    redirect,
    render_template_string,
    request,
    send_file,
    url_for,
)


# Localised helpers from deprecated archive modules
def load_dataframe(path: Path) -> pd.DataFrame:
    """Load CSV/JSON/Excel into a DataFrame."""
    if path.suffix.lower() == ".json":
        return pd.read_json(path)
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    return pd.read_csv(path)


def generate_analytics(df: pd.DataFrame) -> dict:
    """Generate a trivial analytics summary."""
    return {"rows": len(df)}


def enhance_data_with_mappings(
    df: pd.DataFrame, column_mapping: dict[str, str], device_mapping: list[dict]
) -> tuple[pd.DataFrame, None]:
    """Apply column/device mappings to the DataFrame."""
    enhanced_df = df.copy()

    if column_mapping:
        rename_dict = {
            original: mapped for original, mapped in column_mapping.items() if mapped
        }
        if rename_dict:
            enhanced_df = enhanced_df.rename(columns=rename_dict)

    if device_mapping and "door_id" in enhanced_df.columns:
        lookup = {device["door_id"]: device for device in device_mapping}
        enhanced_df["floor_number"] = enhanced_df["door_id"].map(
            lambda x: lookup.get(str(x), {}).get("floor_number", 1)
        )
        enhanced_df["security_level"] = enhanced_df["door_id"].map(
            lambda x: lookup.get(str(x), {}).get("security_level", 5)
        )
        enhanced_df["is_entry"] = enhanced_df["door_id"].map(
            lambda x: lookup.get(str(x), {}).get("is_entry", False)
        )
        enhanced_df["is_exit"] = enhanced_df["door_id"].map(
            lambda x: lookup.get(str(x), {}).get("is_exit", False)
        )

    return enhanced_df, None


def safe_file_write(path: Path, text: str) -> None:
    """Write UTF-8 encoded text to a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


from yosai_intel_dashboard.src.infrastructure.config.constants import API_PORT

app = Flask(__name__)

UPLOAD_HTML = """
<!doctype html>
<title>Investor Demo - Upload</title>
<h1>Upload File</h1>
<form method=post enctype=multipart/form-data action="/upload">
  <input type=file name=file>
  <input type=submit value="Upload">
</form>
"""

COLUMN_HTML = """
<!doctype html>
<title>Investor Demo - Column Mapping</title>
<h1>Step 2: Column Mapping</h1>
<form method=post>
  {% for col in columns %}
    <div>
      <label>{{ col }}</label>
      <select name="{{ col }}">
        {% for opt in options %}
          <option value="{{ opt }}"
            {% if mapping.get(col)==opt %}selected{% endif %}>
            {{ opt or 'Not Mapped' }}
          </option>
        {% endfor %}
      </select>
    </div>
  {% endfor %}
  <input type=submit value="Next">
</form>
"""

DEVICE_HTML = """
<!doctype html>
<title>Investor Demo - Device Mapping</title>
<h1>Step 3: Device Mapping</h1>
<form method=post>
  {% for d in devices %}
    <div>
      <label>{{ d }}</label>
      Floor <input type=number name="floor_{{ d }}" value="1" min="1" max="50">
      Level <input type=number name="sec_{{ d }}" value="5" min="1" max="10">
      Entry <input type=checkbox name="entry_{{ d }}">
      Exit <input type=checkbox name="exit_{{ d }}">
    </div>
  {% endfor %}
  <input type=submit value="Finish">
</form>
"""

RESULT_HTML = """
<!doctype html>
<title>Investor Demo - Results</title>
<h1>Processing Complete</h1>
<a href="{{ url_for('download') }}">Download Results</a>
"""

PIPELINE = [
    "Upload File",
    "Column Mapping",
    "Device Mapping",
    "Generate Analytics",
]

current_df: pd.DataFrame | None = None
column_mapping: dict[str, str] = {}
device_mapping: list[dict[str, object]] = []


def build_stages(current: int) -> list[dict[str, object]]:
    return [
        {"name": name, "complete": idx < current}
        for idx, name in enumerate(PIPELINE, start=1)
    ]


@app.route("/")
def index() -> str:
    """Return the initial file upload page."""
    return render_template_string(UPLOAD_HTML, stages=build_stages(0))


@app.post("/upload")
def upload() -> Response:
    """Save the uploaded file and redirect to column mapping."""
    global current_df, column_mapping, device_mapping
    uploaded = request.files.get("file")
    if not uploaded:
        return redirect(url_for("index"))
    with NamedTemporaryFile(delete=False) as tmp:
        uploaded.save(tmp.name)
        current_df = load_dataframe(Path(tmp.name))
    column_mapping = {}
    device_mapping = []
    return redirect(url_for("map_columns"))


@app.route("/columns", methods=["GET", "POST"])
def map_columns() -> Response:
    """Capture column mappings and show the mapping form."""
    global column_mapping
    if current_df is None:
        return redirect(url_for("index"))
    options = [
        "",
        "person_id",
        "door_id",
        "access_result",
        "timestamp",
        "token_id",
        "event_type",
    ]
    if request.method == "POST":
        column_mapping = {col: request.form.get(col, "") for col in current_df.columns}
        return redirect(url_for("map_devices"))
    sanitized_columns = [html.escape(str(col)) for col in current_df.columns]
    return render_template_string(
        COLUMN_HTML,
        columns=sanitized_columns,
        options=options,
        mapping=column_mapping,
        stages=build_stages(1),
    )


@app.route("/devices", methods=["GET", "POST"])
def map_devices() -> Response:
    """Collect device metadata mappings or skip if none present."""
    global device_mapping
    if current_df is None:
        return redirect(url_for("index"))
    mapped_df, _ = enhance_data_with_mappings(current_df, column_mapping, [])
    if "door_id" not in mapped_df.columns:
        return redirect(url_for("results"))
    devices = list(mapped_df["door_id"].dropna().unique())[:10]
    if request.method == "POST":
        device_mapping = []
        for d in devices:
            device_mapping.append(
                {
                    "door_id": str(d),
                    "floor_number": int(request.form.get(f"floor_{d}", 1)),
                    "security_level": int(request.form.get(f"sec_{d}", 5)),
                    "is_entry": request.form.get(f"entry_{d}") == "on",
                    "is_exit": request.form.get(f"exit_{d}") == "on",
                }
            )
        return redirect(url_for("results"))
    sanitized_devices = [html.escape(str(d)) for d in devices]
    return render_template_string(
        DEVICE_HTML,
        devices=sanitized_devices,
        stages=build_stages(2),
    )


@app.get("/results")
def results() -> Response:
    """Generate analytics output and display the results page."""
    if current_df is None:
        return redirect(url_for("index"))
    enhanced_df, _ = enhance_data_with_mappings(
        current_df, column_mapping, device_mapping
    )
    analytics = generate_analytics(enhanced_df)
    out_path = Path("mvp_output/investor_result.json")
    safe_file_write(out_path, json.dumps(analytics, indent=2))
    return render_template_string(RESULT_HTML, stages=build_stages(3))


@app.route("/download")
def download() -> object:
    return send_file("mvp_output/investor_result.json", as_attachment=True)


if __name__ == "__main__":
    app.run(port=API_PORT)
