import asyncio
import base64

from flask import Blueprint, jsonify, request
from flask_wtf.csrf import validate_csrf

# Use the shared DI container configured at application startup
from core.container import container
from config.service_registration import register_upload_services

if not container.has("upload_processor"):
    register_upload_services(container)

upload_bp = Blueprint("upload", __name__)


@upload_bp.route("/api/v1/upload", methods=["POST"])
def upload_files():
    """Handle file upload and return expected structure for React frontend"""
    try:
        token = (
            request.headers.get("X-CSRFToken")
            or request.headers.get("X-CSRF-Token")
            or request.form.get("csrf_token")
        )
        try:
            validate_csrf(token)
        except Exception:
            return jsonify({"error": "Invalid CSRF token"}), 400

        contents = []
        filenames = []

        # Support both multipart/form-data and raw JSON payloads
        if request.files:
            for file in request.files.values():
                if not file.filename:
                    continue
                file_bytes = file.read()
                b64 = base64.b64encode(file_bytes).decode()
                mime = file.mimetype or "application/octet-stream"
                contents.append(f"data:{mime};base64,{b64}")
                filenames.append(file.filename)
        else:
            data = request.get_json(silent=True) or {}
            contents = data.get("contents", [])
            filenames = data.get("filenames", [])

        # Get services from shared container
        upload_service = container.get("upload_processor")

        # Process files using existing base code
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        result_dict = loop.run_until_complete(
            upload_service.process_uploaded_files(contents, filenames)
        )
        loop.close()

        # Ensure structure matches what React expects
        response = {
            "upload_results": result_dict.get("upload_results", []),
            "file_preview_components": result_dict.get("file_preview_components", []),
            "file_info_dict": {},
        }

        # Process each file's info
        file_info_dict = result_dict.get("file_info_dict", {})
        for filename, info in file_info_dict.items():
            # Get AI column suggestions
            from services.data_enhancer import get_ai_column_suggestions

            df = upload_service.store.get_all_data().get(filename)

            ai_suggestions = {}
            if df is not None:
                ai_suggestions = get_ai_column_suggestions(df)

            response["file_info_dict"][filename] = {
                "filename": filename,
                "rows": info.get("rows", 0),
                "columns": info.get("columns", 0),
                "ai_suggestions": ai_suggestions,
                "column_names": info.get("column_names", []),
            }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
