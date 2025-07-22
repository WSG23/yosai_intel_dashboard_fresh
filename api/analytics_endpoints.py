import asyncio
import json
import logging

from flask import Blueprint, Response, jsonify, request

from config.base import CacheConfig
from core.advanced_cache import AdvancedCacheManager
from services.cached_analytics import CachedAnalyticsService
from services.security import require_permission

logger = logging.getLogger(__name__)

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/v1/analytics")
graphs_bp = Blueprint("graphs", __name__, url_prefix="/api/v1/graphs")
export_bp = Blueprint("export", __name__, url_prefix="/api/v1/export")

# Cached analytics helper
_cache_manager = AdvancedCacheManager(CacheConfig(timeout_seconds=300))
asyncio.run(_cache_manager.start())
_cached_service = CachedAnalyticsService(_cache_manager)

MOCK_DATA = {
    "status": "success",
    "data_summary": {
        "total_records": 1000,
        "unique_users": 50,
        "unique_devices": 25,
        "date_range": {"start": "2024-01-01", "end": "2024-01-31", "span_days": 30},
    },
    "user_patterns": {
        "power_users": ["user1", "user2", "user3"],
        "regular_users": ["user4", "user5"],
        "occasional_users": ["user6", "user7", "user8"],
    },
    "device_patterns": {
        "high_traffic_devices": ["device1", "device2"],
        "moderate_traffic_devices": ["device3", "device4"],
        "low_traffic_devices": ["device5", "device6"],
    },
    "temporal_patterns": {
        "peak_hours": ["09:00", "17:00"],
        "peak_days": ["Monday", "Friday"],
        "hourly_distribution": {"09": 100, "17": 150},
    },
    "access_patterns": {
        "overall_success_rate": 0.85,
        "users_with_low_success": 5,
        "devices_with_low_success": 2,
    },
}


@analytics_bp.route("/patterns", methods=["GET"])
@require_permission("analytics.read")
def get_patterns_analysis():
    facility = request.args.get("facility_id", "default")
    date_range = request.args.get("range", "30d")
    data = asyncio.run(_cached_service.get_analytics_summary(facility, date_range))
    return jsonify(data)


@analytics_bp.route("/sources", methods=["GET"])
@require_permission("analytics.read")
def get_data_sources():
    return jsonify({"sources": [{"value": "test", "label": "Test Data Source"}]})


@analytics_bp.route("/health", methods=["GET"])
@require_permission("analytics.read")
def analytics_health():
    return jsonify({"status": "healthy", "service": "minimal"})


@graphs_bp.route("/chart/<chart_type>", methods=["GET"])
@require_permission("analytics.read")
def get_chart_data(chart_type):
    facility = request.args.get("facility_id", "default")
    date_range = request.args.get("range", "30d")
    data = asyncio.run(_cached_service.get_analytics_summary(facility, date_range))
    if chart_type == "patterns":
        return jsonify({"type": "patterns", "data": data})
    if chart_type == "timeline":
        return jsonify(
            {"type": "timeline", "data": data.get("hourly_distribution", {})}
        )
    return jsonify({"error": "Unknown chart type"}), 400


@export_bp.route("/analytics/json", methods=["GET"])
@require_permission("analytics.read")
def export_analytics_json():
    facility = request.args.get("facility_id", "default")
    date_range = request.args.get("range", "30d")
    data = asyncio.run(_cached_service.get_analytics_summary(facility, date_range))
    response = Response(json.dumps(data, indent=2), mimetype="application/json")
    response.headers["Content-Disposition"] = (
        "attachment; filename=analytics_export.json"
    )
    return response


def register_analytics_blueprints(app):
    app.register_blueprint(analytics_bp)
    app.register_blueprint(graphs_bp)
    app.register_blueprint(export_bp)
    logger.info("Analytics blueprints registered")


@graphs_bp.route("/available-charts", methods=["GET"])
@require_permission("analytics.read")
def get_available_charts():
    """Get list of available chart types."""
    charts = [
        {
            "type": "patterns",
            "name": "Pattern Analysis",
            "description": "User and device pattern analysis",
        },
        {
            "type": "timeline",
            "name": "Timeline Analysis",
            "description": "Temporal pattern analysis",
        },
        {
            "type": "user_activity",
            "name": "User Activity",
            "description": "User behavior patterns",
        },
        {
            "type": "device_usage",
            "name": "Device Usage",
            "description": "Device utilization patterns",
        },
    ]
    return jsonify({"charts": charts})


@export_bp.route("/formats", methods=["GET"])
@require_permission("analytics.read")
def get_export_formats():
    """Get available export formats."""
    formats = [
        {"type": "csv", "name": "CSV", "description": "Comma-separated values"},
        {"type": "json", "name": "JSON", "description": "JavaScript Object Notation"},
        {"type": "xlsx", "name": "Excel", "description": "Microsoft Excel format"},
    ]
    return jsonify({"formats": formats})


@analytics_bp.route("/all", methods=["GET"])
@analytics_bp.route("/<source_type>", methods=["GET"])
@require_permission("analytics.read")
def get_analytics_by_source(source_type="all"):
    """Get analytics data by source type"""
    try:
        facility = request.args.get("facility_id", "default")
        date_range = request.args.get("range", "30d")
        data = asyncio.run(_cached_service.get_analytics_summary(facility, date_range))
        return jsonify(data)
    except Exception as e:
        logger.error(f"Analytics error: {str(e)}")
        return jsonify({"error": str(e)}), 500
