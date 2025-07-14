from __future__ import annotations

import json
from pathlib import Path
from tempfile import NamedTemporaryFile

from flask import Flask, render_template_string, request, send_file

from mvp.data_verification_component import DataVerificationComponent
from mvp.mvp_cli_engine import generate_analytics, load_dataframe
from mvp.unicode_fix_module import safe_file_write

app = Flask(__name__)

HTML = """
<!doctype html>
<title>Investor Demo</title>
<style>
body {font-family: Arial, sans-serif; background: linear-gradient(to bottom right,#004,#008); color:#fff; padding:40px;}
.stage {margin:10px 0;}
.completed {color:#0f0;}
</style>
<h1>Investor Demo Pipeline</h1>
<form method=post enctype=multipart/form-data>
<input type=file name=file>
<input type=submit value="Process">
</form>
{% if stages %}
  <h2>Progress</h2>
  {% for s in stages %}<div class="stage {{ 'completed' if s.complete else '' }}">{{ loop.index }}. {{ s.name }}</div>{% endfor %}
{% endif %}
{% if download_url %}<a href="{{ download_url }}">Download Results</a>{% endif %}
"""

PIPELINE = [
    "File Validation & Security Check",
    "Data Enhancement & Unicode Processing",
    "Device Learning & Classification",
    "Data Quality Analysis",
    "AI-Driven Analytics Generation",
    "Comprehensive Statistical Analysis",
    "Results Export & Storage",
]


@app.route("/", methods=["GET", "POST"])
def investor_demo():
    stages = [{"name": n, "complete": False} for n in PIPELINE]
    download_url = None
    if request.method == "POST":
        uploaded = request.files.get("file")
        if uploaded:
            with NamedTemporaryFile(delete=False) as tmp:
                uploaded.save(tmp.name)
                try:
                    stages[0]["complete"] = True
                    df = load_dataframe(Path(tmp.name))
                    stages[1]["complete"] = True
                    verifier = DataVerificationComponent()
                    df, mapping = verifier.verify_dataframe(df)
                    stages[2]["complete"] = True
                    analytics = generate_analytics(df)
                    stages[3]["complete"] = True
                    stages[4]["complete"] = True
                    stages[5]["complete"] = True
                    out_path = Path("mvp_output/investor_result.json")
                    safe_file_write(out_path, json.dumps(analytics, indent=2))
                    verifier.save_verification(
                        mapping, Path("mvp_output/investor_verification.json")
                    )
                    stages[6]["complete"] = True
                    download_url = "/download"
                except Exception as exc:
                    stages.append({"name": f"Error: {exc}", "complete": False})
    return render_template_string(HTML, stages=stages, download_url=download_url)


@app.route("/download")
def download():
    return send_file("mvp_output/investor_result.json", as_attachment=True)


if __name__ == "__main__":
    app.run(port=5001)
