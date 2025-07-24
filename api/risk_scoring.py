"""REST endpoints exposing risk scoring utilities."""

from __future__ import annotations

from api.adapter import api_adapter
from app import app
from flask import abort, jsonify, request

from analytics.risk_scoring import calculate_risk_score
from core.security_validator import SecurityValidator


@app.route("/api/v1/risk/score", methods=["POST"])
def calculate_score_endpoint():
    """Return aggregated risk score from provided values."""
    payload = request.get_json(silent=True) or {}
    for key, value in payload.items():
        check = SecurityValidator().validate_input(str(value), key)
        if not check["valid"]:
            abort(400, description="Invalid parameter")

    anomaly = float(payload.get("anomaly_score", 0))
    patterns = float(payload.get("pattern_score", 0))
    behavior = float(payload.get("behavior_deviation", 0))

    result = calculate_risk_score(anomaly, patterns, behavior)
    safe = api_adapter.unicode_processor.process_dict(
        {"score": result.score, "level": result.level}
    )
    return jsonify(safe)
