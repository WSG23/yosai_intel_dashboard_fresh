"""
Flask API adapter for Analytics, Graphs, and Export endpoints.
Exposes existing Python services through REST API.
"""

import logging
from typing import Dict, Any, List, Optional
from flask import Blueprint, request, jsonify, Response
from werkzeug.exceptions import BadRequest, InternalServerError
import json
import io
import csv
import pandas as pd
from datetime import datetime

from services.analytics_service import AnalyticsService
from services.protocols.device_learning import DeviceLearningServiceProtocol
from core.unicode import clean_unicode_text, sanitize_dataframe
from core.exceptions import ValidationError

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/v1/analytics')
graphs_bp = Blueprint('graphs', __name__, url_prefix='/api/v1/graphs')
export_bp = Blueprint('export', __name__, url_prefix='/api/v1/export')


class AnalyticsAPIAdapter:
    """Adapter for exposing AnalyticsService through REST API."""

    def __init__(self):
        self.analytics_service = AnalyticsService()

    def get_unique_patterns_analysis(self, data_source: Optional[str] = None) -> Dict[str, Any]:
        """Get unique patterns analysis with error handling."""
        try:
            result = self.analytics_service.get_unique_patterns_analysis(data_source)
            return self._sanitize_response(result)
        except Exception as e:
            logger.error(f"Error in get_unique_patterns_analysis: {e}")
            raise InternalServerError(f"Analytics analysis failed: {str(e)}")

    def get_analytics_by_source(self, source_name: str) -> Dict[str, Any]:
        """Get analytics for specific data source."""
        try:
            # Call existing analytics service method
            result = self.analytics_service.get_analytics_by_source(source_name)
            return self._sanitize_response(result)
        except Exception as e:
            logger.error(f"Error in get_analytics_by_source: {e}")
            raise InternalServerError(f"Source analytics failed: {str(e)}")

    def get_data_sources(self) -> List[Dict[str, str]]:
        """Get available data sources."""
        try:
            sources = self.analytics_service.get_data_source_options()
            return [self._sanitize_response(source) for source in sources]
        except Exception as e:
            logger.error(f"Error getting data sources: {e}")
            return []

    def health_check(self) -> Dict[str, Any]:
        """Check analytics service health."""
        try:
            return self.analytics_service.health_check()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "error", "message": str(e)}

    def _sanitize_response(self, data: Any) -> Any:
        """Sanitize response data to handle Unicode issues."""
        if isinstance(data, dict):
            return {k: self._sanitize_response(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_response(item) for item in data]
        elif isinstance(data, str):
            return clean_unicode_text(data)
        else:
            return data


class GraphsAPIAdapter:
    """Adapter for graph/visualization data."""

    def __init__(self):
        self.analytics_service = AnalyticsService()

    def get_chart_data(self, chart_type: str, data_source: Optional[str] = None) -> Dict[str, Any]:
        """Get data for specific chart type."""
        try:
            if chart_type == "patterns":
                return self._get_patterns_chart_data(data_source)
            elif chart_type == "timeline":
                return self._get_timeline_chart_data(data_source)
            elif chart_type == "user_activity":
                return self._get_user_activity_chart_data(data_source)
            elif chart_type == "device_usage":
                return self._get_device_usage_chart_data(data_source)
            else:
                raise BadRequest(f"Unknown chart type: {chart_type}")
        except Exception as e:
            logger.error(f"Error getting chart data for {chart_type}: {e}")
            raise InternalServerError(f"Chart data failed: {str(e)}")

    def _get_patterns_chart_data(self, data_source: Optional[str]) -> Dict[str, Any]:
        """Get patterns analysis data for charts."""
        analysis = self.analytics_service.get_unique_patterns_analysis(data_source)

        if analysis.get("status") != "success":
            return {"error": "No data available for patterns chart"}

        return {
            "type": "patterns",
            "data": {
                "users": analysis.get("user_patterns", {}),
                "devices": analysis.get("device_patterns", {}),
                "summary": analysis.get("data_summary", {}),
            },
        }

    def _get_timeline_chart_data(self, data_source: Optional[str]) -> Dict[str, Any]:
        """Get timeline data for charts."""
        analysis = self.analytics_service.get_unique_patterns_analysis(data_source)

        if analysis.get("status") != "success":
            return {"error": "No data available for timeline chart"}

        temporal_data = analysis.get("temporal_patterns", {})
        return {
            "type": "timeline",
            "data": {
                "hourly": temporal_data.get("hourly_distribution", {}),
                "daily": temporal_data.get("peak_days", []),
                "peak_hours": temporal_data.get("peak_hours", []),
            },
        }

    def _get_user_activity_chart_data(self, data_source: Optional[str]) -> Dict[str, Any]:
        """Get user activity data for charts."""
        analysis = self.analytics_service.get_unique_patterns_analysis(data_source)

        if analysis.get("status") != "success":
            return {"error": "No data available for user activity chart"}

        user_patterns = analysis.get("user_patterns", {})
        return {
            "type": "user_activity",
            "data": {
                "power_users": user_patterns.get("power_users", []),
                "regular_users": user_patterns.get("regular_users", []),
                "occasional_users": user_patterns.get("occasional_users", []),
            },
        }

    def _get_device_usage_chart_data(self, data_source: Optional[str]) -> Dict[str, Any]:
        """Get device usage data for charts."""
        analysis = self.analytics_service.get_unique_patterns_analysis(data_source)

        if analysis.get("status") != "success":
            return {"error": "No data available for device usage chart"}

        device_patterns = analysis.get("device_patterns", {})
        return {
            "type": "device_usage",
            "data": {
                "high_traffic": device_patterns.get("high_traffic_devices", []),
                "moderate_traffic": device_patterns.get("moderate_traffic_devices", []),
                "low_traffic": device_patterns.get("low_traffic_devices", []),
            },
        }


class ExportAPIAdapter:
    """Adapter for export functionality."""

    def __init__(self):
        self.analytics_service = AnalyticsService()

    def export_analytics_data(self, format_type: str, data_source: Optional[str] = None) -> Response:
        """Export analytics data in specified format."""
        try:
            if format_type not in ["csv", "json", "xlsx"]:
                raise BadRequest(f"Unsupported export format: {format_type}")

            # Get analytics data
            analysis = self.analytics_service.get_unique_patterns_analysis(data_source)

            if analysis.get("status") != "success":
                raise BadRequest("No data available for export")

            if format_type == "csv":
                return self._export_as_csv(analysis)
            elif format_type == "json":
                return self._export_as_json(analysis)
            elif format_type == "xlsx":
                return self._export_as_xlsx(analysis)

        except Exception as e:
            logger.error(f"Export failed: {e}")
            raise InternalServerError(f"Export failed: {str(e)}")

    def _export_as_csv(self, analysis: Dict[str, Any]) -> Response:
        """Export analytics data as CSV."""
        output = io.StringIO()
        writer = csv.writer(output)

        # Write summary data
        writer.writerow(["Analytics Summary"])
        writer.writerow(["Metric", "Value"])

        summary = analysis.get("data_summary", {})
        for key, value in summary.items():
            writer.writerow([key, value])

        writer.writerow([])  # Empty row

        # Write user patterns
        writer.writerow(["User Patterns"])
        user_patterns = analysis.get("user_patterns", {})
        for pattern_type, users in user_patterns.items():
            writer.writerow([pattern_type, len(users) if isinstance(users, list) else users])

        csv_content = output.getvalue()
        output.close()

        response = Response(
            clean_unicode_text(csv_content),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=analytics_export.csv"},
        )
        return response

    def _export_as_json(self, analysis: Dict[str, Any]) -> Response:
        """Export analytics data as JSON."""
        sanitized_data = self._sanitize_for_json(analysis)
        json_content = json.dumps(sanitized_data, indent=2, ensure_ascii=False)

        response = Response(
            json_content,
            mimetype="application/json",
            headers={"Content-Disposition": "attachment; filename=analytics_export.json"},
        )
        return response

    def _export_as_xlsx(self, analysis: Dict[str, Any]) -> Response:
        """Export analytics data as Excel file."""
        try:
            output = io.BytesIO()

            # Create Excel writer
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Summary sheet
                summary_data = analysis.get("data_summary", {})
                summary_df = pd.DataFrame(list(summary_data.items()), columns=["Metric", "Value"])
                summary_df = sanitize_dataframe(summary_df)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)

                # User patterns sheet
                user_patterns = analysis.get("user_patterns", {})
                user_data = []
                for pattern_type, users in user_patterns.items():
                    if isinstance(users, list):
                        for user in users:
                            user_data.append({"pattern_type": pattern_type, "user": user})
                    else:
                        user_data.append({"pattern_type": pattern_type, "count": users})

                if user_data:
                    user_df = pd.DataFrame(user_data)
                    user_df = sanitize_dataframe(user_df)
                    user_df.to_excel(writer, sheet_name='User_Patterns', index=False)

            excel_content = output.getvalue()
            output.close()

            response = Response(
                excel_content,
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=analytics_export.xlsx"},
            )
            return response

        except Exception as e:
            logger.error(f"Excel export failed: {e}")
            raise InternalServerError(f"Excel export failed: {str(e)}")

    def _sanitize_for_json(self, data: Any) -> Any:
        """Sanitize data for JSON serialization."""
        if isinstance(data, dict):
            return {k: self._sanitize_for_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_for_json(item) for item in data]
        elif isinstance(data, str):
            return clean_unicode_text(data)
        elif isinstance(data, (int, float, bool)) or data is None:
            return data
        else:
            return str(data)


# Initialize adapters
analytics_adapter = AnalyticsAPIAdapter()
graphs_adapter = GraphsAPIAdapter()
export_adapter = ExportAPIAdapter()


# Analytics endpoints
@analytics_bp.route('/patterns', methods=['GET'])
def get_patterns_analysis():
    """Get unique patterns analysis."""
    data_source = request.args.get('data_source')
    try:
        result = analytics_adapter.get_unique_patterns_analysis(data_source)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Patterns analysis endpoint failed: {e}")
        return jsonify({"error": str(e)}), 500


@analytics_bp.route('/source/<source_name>', methods=['GET'])
def get_source_analytics(source_name: str):
    """Get analytics for specific source."""
    try:
        result = analytics_adapter.get_analytics_by_source(source_name)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Source analytics endpoint failed: {e}")
        return jsonify({"error": str(e)}), 500


@analytics_bp.route('/sources', methods=['GET'])
def get_data_sources():
    """Get available data sources."""
    try:
        sources = analytics_adapter.get_data_sources()
        return jsonify({"sources": sources})
    except Exception as e:
        logger.error(f"Data sources endpoint failed: {e}")
        return jsonify({"error": str(e)}), 500


@analytics_bp.route('/health', methods=['GET'])
def analytics_health():
    """Analytics service health check."""
    try:
        health = analytics_adapter.health_check()
        return jsonify(health)
    except Exception as e:
        logger.error(f"Analytics health endpoint failed: {e}")
        return jsonify({"error": str(e)}), 500


# Graphs endpoints
@graphs_bp.route('/chart/<chart_type>', methods=['GET'])
def get_chart_data(chart_type: str):
    """Get data for specific chart type."""
    data_source = request.args.get('data_source')
    try:
        result = graphs_adapter.get_chart_data(chart_type, data_source)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Chart data endpoint failed: {e}")
        return jsonify({"error": str(e)}), 500


@graphs_bp.route('/available-charts', methods=['GET'])
def get_available_charts():
    """Get list of available chart types."""
    charts = [
        {"type": "patterns", "name": "Pattern Analysis", "description": "User and device pattern analysis"},
        {"type": "timeline", "name": "Timeline Analysis", "description": "Temporal pattern analysis"},
        {"type": "user_activity", "name": "User Activity", "description": "User behavior patterns"},
        {"type": "device_usage", "name": "Device Usage", "description": "Device utilization patterns"},
    ]
    return jsonify({"charts": charts})


# Export endpoints
@export_bp.route('/analytics/<format_type>', methods=['GET'])
def export_analytics(format_type: str):
    """Export analytics data in specified format."""
    data_source = request.args.get('data_source')
    try:
        return export_adapter.export_analytics_data(format_type, data_source)
    except Exception as e:
        logger.error(f"Export endpoint failed: {e}")
        return jsonify({"error": str(e)}), 500


@export_bp.route('/formats', methods=['GET'])
def get_export_formats():
    """Get available export formats."""
    formats = [
        {"type": "csv", "name": "CSV", "description": "Comma-separated values"},
        {"type": "json", "name": "JSON", "description": "JavaScript Object Notation"},
        {"type": "xlsx", "name": "Excel", "description": "Microsoft Excel format"},
    ]
    return jsonify({"formats": formats})


# Register blueprints function

def register_analytics_blueprints(app):
    """Register all analytics-related blueprints with Flask app."""
    app.register_blueprint(analytics_bp)
    app.register_blueprint(graphs_bp)
    app.register_blueprint(export_bp)
    logger.info("Analytics, graphs, and export blueprints registered")
