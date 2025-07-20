from __future__ import annotations

import json
from pathlib import Path
from tempfile import NamedTemporaryFile

from flask import Flask, render_template_string, request, send_file

from mvp.data_verification_component import DataVerificationComponent
from mvp.mvp_cli_engine import generate_analytics, load_dataframe
from mvp.unicode_fix_module import safe_file_write

app = Flask(__name__)

UPLOAD_FORM = """
<!doctype html>
<title>MVP Upload</title>
<h1>Upload File</h1>
<form method=post enctype=multipart/form-data>
  <input type=file name=file>
  <input type=submit value=Upload>
</form>
{% if message %}<p>{{ message }}</p>{% endif %}
{% if download_url %}<a href="{{ download_url }}">Download Results</a>{% endif %}
"""


@app.route("/", methods=["GET", "POST"])
def upload_file():
    message = None
    download_url = None
    if request.method == "POST":
        uploaded = request.files.get("file")
        if not uploaded:
            message = "No file provided"
        else:
            with NamedTemporaryFile(delete=False) as tmp:
                uploaded.save(tmp.name)
                try:
                    df = load_dataframe(Path(tmp.name))
                    verifier = DataVerificationComponent()
                    df, mapping = verifier.verify_dataframe(df)
                    analytics = generate_analytics(df)
                    out_path = Path("mvp_output/web_result.json")
                    safe_file_write(out_path, json.dumps(analytics, indent=2))
                    verifier.save_verification(
                        mapping, Path("mvp_output/web_verification.json")
                    )
                    download_url = "/download"
                    message = "Processing complete"
                except Exception as exc:
                    message = f"Error: {exc}"
    return render_template_string(
        UPLOAD_FORM, message=message, download_url=download_url
    )


@app.route("/download")
def download():
    return send_file("mvp_output/web_result.json", as_attachment=True)


if __name__ == "__main__":
    app.run(port=5000)
