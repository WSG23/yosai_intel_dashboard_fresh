"""REST endpoints exposing risk scoring utilities."""

from __future__ import annotations

from yosai_intel_dashboard.src.adapters.api.adapter import api_adapter
from app import app
from flask import abort, jsonify, request
from marshmallow import Schema, fields
from flask_apispec import doc, marshal_with, use_kwargs

from analytics.risk_scoring import calculate_risk_score
from validation.security_validator import SecurityValidator


class RiskInputSchema(Schema):
    anomaly_score = fields.Float(load_default=0)
    pattern_score = fields.Float(load_default=0)
    behavior_deviation = fields.Float(load_default=0)


class RiskResponseSchema(Schema):
    score = fields.Float()
    level = fields.String()


@app.route("/api/v1/risk/score", methods=["POST"])
@doc(description="Calculate risk score", tags=["risk"])
@use_kwargs(RiskInputSchema, location="json")
@marshal_with(RiskResponseSchema)
def calculate_score_endpoint(**payload):
    """Return aggregated risk score from provided values."""
    payload = payload or {}
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
