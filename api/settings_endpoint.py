import json
import os

from filelock import FileLock
from flask import Blueprint, jsonify, request
from flask_apispec import doc
from error_handling import ErrorCategory, ErrorHandler
from yosai_framework.errors import CODE_TO_STATUS
from shared.errors.types import ErrorCode
from pydantic import BaseModel

from utils.pydantic_decorators import validate_input, validate_output

settings_bp = Blueprint("settings", __name__)

handler = ErrorHandler()


class SettingsSchema(BaseModel):
    theme: str | None = None
    itemsPerPage: int | None = None

SETTINGS_FILE = os.getenv(
    "YOSAI_SETTINGS_FILE",
    os.path.join(os.path.dirname(__file__), "user_settings.json"),
)
LOCK_FILE = f"{SETTINGS_FILE}.lock"
DEFAULT_SETTINGS = {
    "theme": "light",
    "itemsPerPage": 10,
}


def _load_settings():
    if os.path.exists(SETTINGS_FILE):
        lock = FileLock(LOCK_FILE)
        try:
            with lock:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
    return DEFAULT_SETTINGS.copy()


def _save_settings(settings: dict) -> None:
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    lock = FileLock(LOCK_FILE)
    with lock:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f)


@settings_bp.route("/api/v1/settings", methods=["GET"])
@doc(description="Get user settings", tags=["settings"])
@validate_output(SettingsSchema)
def get_settings():
    """Return saved user settings or defaults."""
    settings = _load_settings()
    return settings, 200


@settings_bp.route("/api/v1/settings", methods=["POST", "PUT"])
@doc(description="Update user settings", tags=["settings"])
@validate_input(SettingsSchema)
@validate_output(SettingsSchema)
def update_settings(payload: SettingsSchema):
    """Update and persist user settings."""
    data = payload.dict(exclude_none=True)
    settings = _load_settings()
    settings.update(data)
    try:
        _save_settings(settings)
    except Exception as exc:
        err = handler.handle(exc, ErrorCategory.INTERNAL)
        return jsonify(err.to_dict()), CODE_TO_STATUS[ErrorCode.INTERNAL]
    return {"status": "success", "settings": settings}, 200
