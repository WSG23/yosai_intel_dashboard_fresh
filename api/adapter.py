from __future__ import annotations

"""Complete API adapter bridging React frontend with Python services."""

import asyncio
import base64
import logging
import uuid
from datetime import datetime
from functools import wraps
from typing import Any, Dict, List

import pandas as pd
from flask import Blueprint, jsonify, request
from flask_cors import cross_origin
from flask_socketio import SocketIO, emit, join_room

from components import column_verification
from components.simple_device_mapping import generate_ai_device_defaults
from core.security_validator import SecurityValidator
from core.unicode import UnicodeProcessor
from services.ai_mapping_store import ai_mapping_store
from services.analytics_service import get_analytics_service
from services.data_enhancer import apply_manual_mapping
from services.interfaces import get_device_learning_service
from services.upload.core.processor import UploadProcessingService
from utils.upload_store import uploaded_data_store

logger = logging.getLogger(__name__)

# API Blueprint
api_bp = Blueprint("api", __name__, url_prefix="/api/v1")

# SocketIO instance
socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode="threading",
    logger=True,
    engineio_logger=True,
)


class APIAdapter:
    """Complete API adapter bridging React frontend with Python services."""

    def __init__(self) -> None:
        self.validator = SecurityValidator()
        self.unicode_processor = UnicodeProcessor()
        self.analytics_service = None
        self.upload_service = None
        self.container = None
        self._active_tasks: Dict[str, Dict[str, Any]] = {}

    def initialize(self, app: Any, container: Any) -> None:
        """Initialize services from app container"""
        self.container = container

        try:
            self.analytics_service = container.get("analytics_service")
            self.upload_service = container.get("upload_service")

            if not self.upload_service:
                self.upload_service = UploadProcessingService()

            logger.info("API Adapter initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize API adapter: {e}")
            raise


# Initialize adapter
api_adapter = APIAdapter()


# Error handler decorator


def handle_errors(f):
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"API error in {f.__name__}: {str(e)}", exc_info=True)
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": str(e),
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                ),
                500,
            )

    return decorated_function


# ============= Analytics Endpoints =============


@api_bp.route("/analytics/summary", methods=["GET"])
@cross_origin()
@handle_errors
def get_analytics_summary():
    """Get analytics summary with full compatibility"""
    data_source = request.args.get("data_source", "uploaded")

    validation_result = api_adapter.validator.validate_input(data_source, "data_source")
    if not validation_result["valid"]:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Invalid data source",
                    "issues": validation_result["issues"],
                }
            ),
            400,
        )

    service = get_analytics_service()
    if not service:
        return (
            jsonify({"status": "error", "message": "Analytics service unavailable"}),
            503,
        )

    if data_source == "uploaded" or data_source.startswith("upload:"):
        result = service.get_analytics_from_uploaded_data()
    else:
        result = service.get_analytics_by_source(data_source)

    safe_result = api_adapter.unicode_processor.process_dict(result)

    return jsonify(
        {
            "status": "success",
            "data": safe_result,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


@api_bp.route("/analytics/patterns", methods=["GET"])
@cross_origin()
@handle_errors
def get_patterns_analysis():
    """Get unique patterns analysis with progress tracking"""
    data_source = request.args.get("data_source")
    force_refresh = request.args.get("force_refresh", "false").lower() == "true"

    service = get_analytics_service()
    if not service:
        return jsonify({"status": "error", "message": "Service unavailable"}), 503

    if force_refresh and hasattr(service, "_cache"):
        service._cache.clear()

    result = service.get_unique_patterns_analysis(data_source)
    safe_result = api_adapter.unicode_processor.process_dict(result)

    return jsonify(safe_result)


@api_bp.route("/analytics/sources", methods=["GET"])
@cross_origin()
@handle_errors
def get_data_sources():
    """Get all available data sources"""
    from pages.deep_analytics_complex.analysis import get_data_source_options_safe

    options = get_data_source_options_safe()

    enriched_options: List[Dict[str, Any]] = []
    for option in options:
        enriched = {
            **option,
            "type": "upload" if option["value"].startswith("upload:") else "service",
            "available": True,
        }

        if enriched["type"] == "upload":
            filename = option["value"].replace("upload:", "")
            enriched["metadata"] = {
                "filename": filename,
                "exists": filename in uploaded_data_store.get_filenames(),
            }

        enriched_options.append(enriched)

    return jsonify(
        {
            "sources": enriched_options,
            "default": "uploaded",
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


@api_bp.route("/analytics/analyze", methods=["POST"])
@cross_origin()
@handle_errors
def analyze_data():
    """Run specific analysis on data"""
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    data_source = data.get("data_source", "uploaded")
    analysis_type = data.get("analysis_type", "summary")

    from services.data_processing.analytics_engine import (
        analyze_data_with_service,
        run_ai_analysis,
        run_quality_analysis,
    )

    if analysis_type == "ai_suggest":
        result = run_ai_analysis(data_source)
    elif analysis_type == "quality":
        result = run_quality_analysis(data_source)
    else:
        result = analyze_data_with_service(data_source, analysis_type)

    return jsonify(result)


# ============= File Upload Endpoints =============


@api_bp.route("/upload/file", methods=["POST"])
@cross_origin()
@handle_errors
async def upload_file():
    """Handle file upload with progress tracking"""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    files = request.files.getlist("file")
    if not files or files[0].filename == "":
        return jsonify({"error": "No file selected"}), 400

    task_id = str(uuid.uuid4())

    results: List[Dict[str, Any]] = []
    for file in files:
        try:
            content = file.read()

            validation = api_adapter.validator.validate_file_upload(
                file.filename,
                content,
            )
            if not validation["valid"]:
                results.append(
                    {
                        "filename": file.filename,
                        "status": "error",
                        "message": "Validation failed",
                        "issues": validation["issues"],
                    }
                )
                continue

            content_b64 = base64.b64encode(content).decode("utf-8")
            content_str = f"data:{file.content_type};base64,{content_b64}"

            def progress_callback(current: int, total: int = 100) -> None:
                progress = int((current / total) * 100) if total > 0 else 0
                socketio.emit(
                    "upload_progress",
                    {
                        "task_id": task_id,
                        "filename": file.filename,
                        "progress": progress,
                        "current": current,
                        "total": total,
                    },
                    room=task_id,
                )

            processor = api_adapter.upload_service or UploadProcessingService()

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            result = await processor.process_uploaded_files(
                [content_str],
                [file.filename],
                task_progress=progress_callback,
            )

            results.append(
                {
                    "filename": file.filename,
                    "status": "success",
                    "task_id": task_id,
                    "result": result,
                }
            )

        except Exception as e:
            logger.error(f"Upload error for {file.filename}: {e}")
            results.append(
                {
                    "filename": file.filename,
                    "status": "error",
                    "message": str(e),
                }
            )

    return jsonify(
        {
            "task_id": task_id,
            "results": results,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


@api_bp.route("/upload/status/<task_id>", methods=["GET"])
@cross_origin()
@handle_errors
def get_upload_status(task_id: str):
    """Get upload task status"""
    if task_id in api_adapter._active_tasks:
        task = api_adapter._active_tasks[task_id]
        return jsonify(
            {
                "task_id": task_id,
                "status": task.get("status", "processing"),
                "progress": task.get("progress", 0),
                "result": task.get("result"),
            }
        )

    return jsonify({"task_id": task_id, "status": "not_found"}), 404


@api_bp.route("/upload/files", methods=["GET"])
@cross_origin()
@handle_errors
def get_uploaded_files():
    """Get list of uploaded files"""
    try:
        filenames = uploaded_data_store.get_filenames()

        file_info: List[Dict[str, Any]] = []
        for filename in filenames:
            df = uploaded_data_store.load_dataframe(filename)
            info = {
                "filename": filename,
                "rows": len(df),
                "columns": len(df.columns),
                "size_mb": df.memory_usage(deep=True).sum() / 1024 / 1024,
                "columns_list": list(df.columns),
                "uploaded_at": datetime.utcnow().isoformat(),
            }
            file_info.append(info)

        return jsonify({"files": file_info, "total": len(file_info)})
    except Exception as e:
        logger.error(f"Error getting uploaded files: {e}")
        return jsonify({"files": [], "total": 0, "error": str(e)})


@api_bp.route("/upload/column-suggestions", methods=["POST"])
@cross_origin()
@handle_errors
def get_column_suggestions():
    """Return AI column mapping suggestions for uploaded data."""
    data = request.get_json() or {}
    filename = data.get("filename", "")
    columns = data.get("columns", [])
    sample_data = data.get("sample_data", {})

    if not filename or not columns:
        return jsonify({"status": "error", "message": "Invalid parameters"}), 400

    validation = api_adapter.validator.validate_input(filename, "filename")
    if not validation["valid"]:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Invalid filename",
                    "issues": validation["issues"],
                }
            ),
            400,
        )

    try:
        df = pd.DataFrame(sample_data, columns=columns)
    except Exception:
        df = pd.DataFrame(sample_data)

    suggestions = column_verification.get_ai_column_suggestions(df, filename)

    return jsonify(
        {
            "suggestions": suggestions,
            "required_fields": [
                "timestamp",
                "person_id",
                "door_id",
                "access_result",
            ],
        }
    )


@api_bp.route("/upload/device-mappings", methods=["POST"])
@cross_origin()
@handle_errors
def get_device_mappings():
    """Provide device mapping suggestions using AI learning."""
    data = request.get_json() or {}
    filename = data.get("filename", "")
    devices: List[str] = data.get("devices", [])

    if not filename or not isinstance(devices, list):
        return jsonify({"status": "error", "message": "Invalid parameters"}), 400

    learning_service = get_device_learning_service(api_adapter.container)

    mappings: Dict[str, Dict[str, Any]] = {}
    unknown_devices: List[str] = []

    for dev in devices:
        learned = learning_service.get_device_mapping_by_name(dev)
        if learned:
            mappings[dev] = learned
        else:
            unknown_devices.append(dev)

    if unknown_devices:
        df = pd.DataFrame({"door_id": unknown_devices})
        generate_ai_device_defaults(df, "auto")
        for dev in unknown_devices:
            mappings[dev] = ai_mapping_store.get(dev)

    clean = {
        d: {
            "floor_number": m.get("floor_number"),
            "is_entry": m.get("is_entry"),
            "is_exit": m.get("is_exit"),
            "security_level": m.get("security_level"),
            "confidence": m.get("confidence"),
        }
        for d, m in mappings.items()
    }

    return jsonify({"mappings": clean})


@api_bp.route("/upload/save-mappings", methods=["POST"])
@cross_origin()
@handle_errors
def save_mappings():
    """Persist verified column and device mappings."""
    data = request.get_json() or {}
    filename = data.get("filename")
    column_mappings = data.get("column_mappings", {})
    device_mappings = data.get("device_mappings", {})

    if not filename:
        return jsonify({"status": "error", "message": "Filename required"}), 400

    df = uploaded_data_store.load_dataframe(filename)
    column_verification.save_verified_mappings(df, filename, column_mappings, {})

    learning_service = get_device_learning_service(api_adapter.container)
    verified = {
        d: m
        for d, m in device_mappings.items()
        if isinstance(m, dict) and m.get("manually_verified")
    }
    if verified:
        learning_service.save_user_device_mappings(df, filename, verified)

    return jsonify({"status": "success"})


@api_bp.route("/upload/apply-mappings", methods=["POST"])
@cross_origin()
@handle_errors
def apply_mappings():
    """Apply provided column mappings to stored data."""
    data = request.get_json() or {}
    filename = data.get("filename")
    column_mappings = data.get("column_mappings", {})

    if not filename:
        return jsonify({"status": "error", "message": "Filename required"}), 400

    df = uploaded_data_store.load_dataframe(filename)
    processed = apply_manual_mapping(df, column_mappings)
    uploaded_data_store.add_file(filename, processed)

    devices = (
        sorted(processed["door_id"].dropna().unique().tolist())
        if "door_id" in processed.columns
        else []
    )

    return jsonify({"devices": devices, "filename": filename, "processed": True})


# ============= WebSocket Event Handlers =============


@socketio.on("connect")
def handle_connect():
    """Handle client connection"""
    client_id = request.sid
    logger.info(f"Client connected: {client_id}")

    emit(
        "connected",
        {
            "client_id": client_id,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
        },
    )


@socketio.on("disconnect")
def handle_disconnect():
    """Handle client disconnection"""
    client_id = request.sid
    logger.info(f"Client disconnected: {client_id}")


@socketio.on("subscribe_analytics")
def handle_analytics_subscription(data: Dict[str, Any]):
    """Subscribe to real-time analytics updates"""
    room = data.get("room", "analytics")
    join_room(room)

    try:
        service = get_analytics_service()
        if service:
            summary = service.get_dashboard_summary()
            safe_summary = api_adapter.unicode_processor.process_dict(summary)

            emit(
                "analytics_update",
                {
                    "type": "initial",
                    "data": safe_summary,
                    "timestamp": datetime.utcnow().isoformat(),
                },
                room=room,
            )
    except Exception as e:
        logger.error(f"Error sending initial analytics: {e}")
        emit(
            "analytics_error",
            {"error": str(e), "timestamp": datetime.utcnow().isoformat()},
        )


@socketio.on("join_upload_room")
def handle_join_upload(data: Dict[str, Any]):
    """Join upload progress room"""
    task_id = data.get("task_id")
    if task_id:
        join_room(task_id)
        logger.debug(f"Client {request.sid} joined upload room {task_id}")


@socketio.on("request_data_refresh")
def handle_data_refresh(data: Dict[str, Any]):
    """Handle request for data refresh"""
    data_type = data.get("type", "analytics")

    try:
        if data_type == "analytics":
            service = get_analytics_service()
            if service:
                if hasattr(service, "_cache"):
                    service._cache.clear()

                summary = service.get_dashboard_summary()
                emit(
                    "data_refreshed",
                    {
                        "type": data_type,
                        "data": summary,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )
    except Exception as e:
        emit("refresh_error", {"error": str(e), "type": data_type})


# ============= Health & Status Endpoints =============


@api_bp.route("/health", methods=["GET"])
@cross_origin()
def health_check():
    """API health check"""
    try:
        analytics_ok = api_adapter.analytics_service is not None
        upload_ok = api_adapter.upload_service is not None

        db_ok = False
        try:
            if api_adapter.container:
                db = api_adapter.container.get("database")
                if db:
                    db.execute_query("SELECT 1")
                    db_ok = True
        except Exception:
            pass

        return jsonify(
            {
                "status": "healthy" if all([analytics_ok, upload_ok]) else "degraded",
                "services": {
                    "analytics": analytics_ok,
                    "upload": upload_ok,
                    "database": db_ok,
                },
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0.0",
            }
        )
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500


# Export functions for app integration


def initialize_api(app: Any, container: Any) -> None:
    """Initialize API with app and container"""
    api_adapter.initialize(app, container)
    app.register_blueprint(api_bp)
    socketio.init_app(app)
    logger.info("API routes registered successfully")
