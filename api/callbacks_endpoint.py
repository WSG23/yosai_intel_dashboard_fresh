from flask import Blueprint, jsonify, request

"""Expose legacy Dash callback logic as Flask endpoints."""


callbacks_bp = Blueprint("callbacks", __name__, url_prefix="/api/v1/callbacks")


@callbacks_bp.post("/toggle-custom-field")
def api_toggle_custom_field():
    from components.column_verification import toggle_custom_field
    data = request.get_json(force=True)
    selected_value = data.get("selected_value")
    result = toggle_custom_field(selected_value)
    return jsonify(result)


@callbacks_bp.post("/save-column-mappings")
def api_save_column_mappings():
    from components.column_verification import save_column_mappings_callback
    payload = request.get_json(force=True)
    n_clicks = payload.get("n_clicks")
    column_values = payload.get("column_values", [])
    custom_values = payload.get("custom_values", [])
    uploaded_files = payload.get("uploaded_files", {})
    message, color = save_column_mappings_callback(
        n_clicks, column_values, custom_values, uploaded_files
    )
    return jsonify({"message": message, "color": color})


@callbacks_bp.post("/toggle-device-verification")
def api_toggle_device_verification():
    from components.device_verification import toggle_device_verification_modal
    data = request.get_json(force=True)
    confirm = data.get("confirm_clicks")
    cancel = data.get("cancel_clicks")
    is_open = data.get("is_open", False)
    result = toggle_device_verification_modal(confirm, cancel, is_open)
    return jsonify({"is_open": result})


@callbacks_bp.post("/mark-device-edited")
def api_mark_device_edited():
    from components.device_verification import mark_device_as_edited
    data = request.get_json(force=True)
    floor = data.get("floor")
    access = data.get("access")
    special = data.get("special")
    security = data.get("security")
    result = mark_device_as_edited(floor, access, special, security)
    return jsonify({"edited": result})


@callbacks_bp.post("/toggle-simple-device-modal")
def api_toggle_simple_device_modal():
    from components.simple_device_mapping import toggle_simple_device_modal
    data = request.get_json(force=True)
    open_clicks = data.get("open_clicks")
    cancel_clicks = data.get("cancel_clicks")
    save_clicks = data.get("save_clicks")
    is_open = data.get("is_open", False)
    result = toggle_simple_device_modal(open_clicks, cancel_clicks, save_clicks, is_open)
    return jsonify({"is_open": result})


@callbacks_bp.post("/save-user-inputs")
def api_save_user_inputs():
    from components.simple_device_mapping import save_user_inputs
    data = request.get_json(force=True)
    floors = data.get("floors", [])
    security = data.get("security", [])
    access = data.get("access", [])
    special = data.get("special", [])
    devices = data.get("devices", [])
    status = save_user_inputs(floors, security, access, special, devices)
    return jsonify({"status": status})


@callbacks_bp.post("/apply-ai-device-suggestions")
def api_apply_ai_device_suggestions():
    from components.simple_device_mapping import apply_ai_device_suggestions
    data = request.get_json(force=True)
    suggestions = data.get("suggestions", {})
    devices = data.get("devices", [])
    floors, access, special, security = apply_ai_device_suggestions(suggestions, devices)
    return jsonify({
        "floors": floors,
        "access": access,
        "special": special,
        "security": security,
    })


@callbacks_bp.post("/populate-simple-device-modal")
def api_populate_simple_device_modal():
    from components.simple_device_mapping import populate_simple_device_modal
    data = request.get_json(force=True)
    is_open = data.get("is_open", False)
    result = populate_simple_device_modal(is_open)
    if isinstance(result, tuple) or hasattr(result, "to_plotly_json"):
        return jsonify({"error": "unsupported return type"}), 400
    if isinstance(result, dict) and "props" in result:
        return jsonify({"error": "dash component returned"}), 400
    # When using the service directly, the function returns a Modal or dash.no_update.
    # For the API we simplify: True if modal should open otherwise False.
    return jsonify({"open": result is not None})
