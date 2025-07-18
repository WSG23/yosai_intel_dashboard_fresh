import json
import os
from flask import Blueprint, jsonify, request

settings_bp = Blueprint('settings', __name__)

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), 'user_settings.json')
DEFAULT_SETTINGS = {
    'theme': 'light',
    'itemsPerPage': 10,
}

def _load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_SETTINGS.copy()


def _save_settings(settings: dict) -> None:
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f)


@settings_bp.route('/api/v1/settings', methods=['GET'])
def get_settings():
    """Return saved user settings or defaults."""
    settings = _load_settings()
    return jsonify(settings), 200


@settings_bp.route('/api/v1/settings', methods=['POST', 'PUT'])
def update_settings():
    """Update and persist user settings."""
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid payload'}), 400
    settings = _load_settings()
    settings.update(data)
    try:
        _save_settings(settings)
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500
    return jsonify({'status': 'success', 'settings': settings}), 200

