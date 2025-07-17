import logging
from typing import Dict, Any, List, Optional
from flask import Blueprint, request, jsonify, Response
import json

logger = logging.getLogger(__name__)

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/v1/analytics')
graphs_bp = Blueprint('graphs', __name__, url_prefix='/api/v1/graphs')
export_bp = Blueprint('export', __name__, url_prefix='/api/v1/export')

MOCK_DATA = {
    "status": "success",
    "data_summary": {
        "total_records": 1000,
        "unique_users": 50,
        "unique_devices": 25,
        "date_range": {"start": "2024-01-01", "end": "2024-01-31", "span_days": 30}
    },
    "user_patterns": {
        "power_users": ["user1", "user2", "user3"],
        "regular_users": ["user4", "user5"],
        "occasional_users": ["user6", "user7", "user8"]
    },
    "device_patterns": {
        "high_traffic_devices": ["device1", "device2"],
        "moderate_traffic_devices": ["device3", "device4"],
        "low_traffic_devices": ["device5", "device6"]
    },
    "temporal_patterns": {
        "peak_hours": ["09:00", "17:00"],
        "peak_days": ["Monday", "Friday"],
        "hourly_distribution": {"09": 100, "17": 150}
    },
    "access_patterns": {
        "overall_success_rate": 0.85,
        "users_with_low_success": 5,
        "devices_with_low_success": 2
    }
}

@analytics_bp.route('/patterns', methods=['GET'])
def get_patterns_analysis():
    return jsonify(MOCK_DATA)

@analytics_bp.route('/sources', methods=['GET'])
def get_data_sources():
    return jsonify({"sources": [{"value": "test", "label": "Test Data Source"}]})

@analytics_bp.route('/health', methods=['GET'])
def analytics_health():
    return jsonify({"status": "healthy", "service": "minimal"})

@graphs_bp.route('/chart/<chart_type>', methods=['GET'])
def get_chart_data(chart_type):
    if chart_type == "patterns":
        return jsonify({"type": "patterns", "data": MOCK_DATA})
    elif chart_type == "timeline":
        return jsonify({"type": "timeline", "data": MOCK_DATA["temporal_patterns"]})
    return jsonify({"error": "Unknown chart type"}), 400

@export_bp.route('/analytics/json', methods=['GET'])
def export_analytics_json():
    response = Response(json.dumps(MOCK_DATA, indent=2), mimetype="application/json")
    response.headers["Content-Disposition"] = "attachment; filename=analytics_export.json"
    return response

def register_analytics_blueprints(app):
    app.register_blueprint(analytics_bp)
    app.register_blueprint(graphs_bp)
    app.register_blueprint(export_bp)
    logger.info("Analytics blueprints registered")

@graphs_bp.route('/available-charts', methods=['GET'])
def get_available_charts():
    """Get list of available chart types."""
    charts = [
        {"type": "patterns", "name": "Pattern Analysis", "description": "User and device pattern analysis"},
        {"type": "timeline", "name": "Timeline Analysis", "description": "Temporal pattern analysis"},
        {"type": "user_activity", "name": "User Activity", "description": "User behavior patterns"},
        {"type": "device_usage", "name": "Device Usage", "description": "Device utilization patterns"}
    ]
    return jsonify({"charts": charts})

@export_bp.route('/formats', methods=['GET'])
def get_export_formats():
    """Get available export formats."""
    formats = [
        {"type": "csv", "name": "CSV", "description": "Comma-separated values"},
        {"type": "json", "name": "JSON", "description": "JavaScript Object Notation"},
        {"type": "xlsx", "name": "Excel", "description": "Microsoft Excel format"}
    ]
    return jsonify({"formats": formats})

@analytics_bp.route('/all', methods=['GET'])
@analytics_bp.route('/<source_type>', methods=['GET'])
def get_analytics_by_source(source_type='all'):
    """Get analytics data by source type"""
    try:
        # Return mock data matching the React component's expected format
        return jsonify({
            'total_records': 15234,
            'unique_devices': 47,
            'date_range': {
                'start': '2024-01-01',
                'end': '2024-12-31'
            },
            'patterns': [
                {'pattern': 'Port Scan Detected', 'count': 523, 'percentage': 35},
                {'pattern': 'Brute Force Attempt', 'count': 312, 'percentage': 25},
                {'pattern': 'Suspicious Traffic', 'count': 245, 'percentage': 20},
                {'pattern': 'Policy Violation', 'count': 198, 'percentage': 15},
                {'pattern': 'Malware Detected', 'count': 67, 'percentage': 5}
            ],
            'device_distribution': [
                {'device': 'Firewall-01', 'count': 8234},
                {'device': 'Router-Main', 'count': 4521},
                {'device': 'Switch-Core', 'count': 2479}
            ]
        })
    except Exception as e:
        logger.error(f"Analytics error: {str(e)}")
        return jsonify({'error': str(e)}), 500
