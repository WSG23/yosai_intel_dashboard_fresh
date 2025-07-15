from __future__ import annotations

import json
from pathlib import Path
from tempfile import NamedTemporaryFile

import pandas as pd
from flask import (
    Flask,
    redirect,
    render_template_string,
    request,
    send_file,
    url_for,
)

from mvp_cli_engine import generate_analytics, load_dataframe
from simple_mapping_interface import enhance_data_with_mappings
from unicode_fix_module import safe_file_write

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
    return render_template_string(UPLOAD_HTML, stages=build_stages(0))


@app.post("/upload")
def upload() -> object:
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
def map_columns() -> object:
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
    return render_template_string(
        COLUMN_HTML,
        columns=current_df.columns,
        options=options,
        mapping=column_mapping,
        stages=build_stages(1),
    )


@app.route("/devices", methods=["GET", "POST"])
def map_devices() -> object:
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
    return render_template_string(
        DEVICE_HTML,
        devices=devices,
        stages=build_stages(2),
    )


@app.get("/results")
def results() -> object:
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
    app.run(port=5001)
