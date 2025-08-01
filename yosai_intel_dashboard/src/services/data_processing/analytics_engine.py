# Utility functions and analytics algorithms extracted from page modules.
import logging
from functools import lru_cache
from typing import Any, Dict, List, Optional

import pandas as pd

from services import get_analytics_service  # type: ignore

try:
    from yosai_intel_dashboard.src.services.ai_suggestions import generate_column_suggestions

    AI_SUGGESTIONS_AVAILABLE = True
except Exception:  # pragma: no cover - optional AI suggestions
    AI_SUGGESTIONS_AVAILABLE = False

    def generate_column_suggestions(
        *args: Any, **kwargs: Any
    ) -> Dict[str, Dict[str, Any]]:
        return {}


from yosai_intel_dashboard.src.core.interfaces.service_protocols import get_upload_data_service
from yosai_intel_dashboard.src.utils.preview_utils import serialize_dataframe_preview
from validation.unicode_validator import UnicodeValidator

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Analytics service helpers
# ---------------------------------------------------------------------------


def get_data_source_options_safe() -> List[Dict[str, str]]:
    """Return dropdown options for available data sources."""
    options: List[Dict[str, str]] = []
    try:
        from yosai_intel_dashboard.src.services.upload_data_service import get_uploaded_data  # lazy import

        uploaded_files = get_uploaded_data(get_upload_data_service())
        for filename in uploaded_files.keys():
            options.append(
                {"label": f"File: {filename}", "value": f"upload:{filename}"}
            )
    except Exception:
        pass
    try:
        service = get_analytics_service()
        if service:
            service_sources = service.get_data_source_options()
            for source_dict in service_sources:
                if isinstance(source_dict, dict):
                    label = source_dict.get("label", "Unknown")
                    value = source_dict.get("value", "unknown")
                else:
                    label = str(source_dict)
                    value = str(source_dict)
                options.append(
                    {"label": f"Service: {label}", "value": f"service:{value}"}
                )
    except Exception as exc:  # pragma: no cover - best effort
        logger.exception("Error getting service data sources: %s", exc)
    if not options:
        options.append(
            {"label": "No data sources available - Upload files first", "value": "none"}
        )
    return options


def get_latest_uploaded_source_value() -> Optional[str]:
    """Return the dropdown value for the most recently uploaded file."""
    try:
        from yosai_intel_dashboard.src.services.upload_data_service import get_uploaded_filenames  # lazy import

        filenames = get_uploaded_filenames(get_upload_data_service())
        if filenames:
            return f"upload:{filenames[-1]}"
    except ImportError as exc:  # pragma: no cover - best effort
        logger.error("File upload utilities missing: %s", exc)
    except Exception as exc:  # pragma: no cover - best effort
        logger.exception("Failed to get latest uploaded source value: %s", exc)
    return None


def get_analysis_type_options() -> List[Dict[str, str]]:
    """Return available analysis types including AI suggestions."""
    return [
        {"label": "🔒 Security Patterns", "value": "security"},
        {"label": "📈 Access Trends", "value": "trends"},
        {"label": "👤 User Behavior", "value": "behavior"},
        {"label": "🚨 Anomaly Detection", "value": "anomaly"},
        {"label": "🤖 AI Column Suggestions", "value": "suggests"},
        {"label": "📊 Data Quality", "value": "quality"},
    ]


def clean_analysis_data_unicode(df: pd.DataFrame) -> pd.DataFrame:
    """Return DataFrame sanitized for Unicode issues."""
    validator = UnicodeValidator()
    try:
        return UnicodeValidator().validate_dataframe(df)

    except Exception as exc:  # pragma: no cover - best effort
        logger.exception("Unicode sanitization failed: %s", exc)
        return df


# ---------------------------------------------------------------------------
# AI suggestion helpers
# ---------------------------------------------------------------------------


def get_ai_suggestions_for_file(
    df: pd.DataFrame, filename: str
) -> Dict[str, Dict[str, Any]]:
    """Return AI column suggestions for ``df`` columns."""
    try:
        return generate_column_suggestions(list(df.columns))
    except Exception:
        suggestions: Dict[str, Dict[str, Any]] = {}
        for col in df.columns:
            col_lower = col.lower().strip()
            if any(word in col_lower for word in ["time", "date", "stamp"]):
                suggestions[col] = {"field": "timestamp", "confidence": 0.8}
            elif any(word in col_lower for word in ["person", "user", "employee"]):
                suggestions[col] = {"field": "person_id", "confidence": 0.7}
            elif any(word in col_lower for word in ["door", "location", "device"]):
                suggestions[col] = {"field": "door_id", "confidence": 0.7}
            elif any(word in col_lower for word in ["access", "result", "status"]):
                suggestions[col] = {"field": "access_result", "confidence": 0.6}
            elif any(word in col_lower for word in ["token", "badge", "card"]):
                suggestions[col] = {"field": "token_id", "confidence": 0.6}
            else:
                suggestions[col] = {"field": "", "confidence": 0.0}
        return suggestions


# ---------------------------------------------------------------------------
# Analysis processors
# ---------------------------------------------------------------------------


@lru_cache(maxsize=32)
def process_suggests_analysis(data_source: str) -> Dict[str, Any]:
    """Process AI suggestions analysis for the selected data source."""
    try:
        if not data_source or data_source == "none":
            return {"error": "No data source selected"}

        if data_source.startswith("upload:") or data_source == "service:uploaded":
            if data_source.startswith("upload:"):
                filename = data_source.replace("upload:", "")
            else:
                filename = None

            from yosai_intel_dashboard.src.services.upload_data_service import get_uploaded_data  # lazy import

            uploaded_files = get_uploaded_data()
            if not uploaded_files:
                return {"error": "No uploaded files found"}
            if filename is None or filename not in uploaded_files:
                filename = list(uploaded_files.keys())[0]

            df = uploaded_files[filename]

            try:
                suggestions = get_ai_suggestions_for_file(df, filename)
            except Exception as exc:  # pragma: no cover - best effort
                logger.exception("AI suggestions failed: %s", exc)
                return {"error": f"AI suggestions failed: {str(exc)}"}

            processed_suggestions: List[Dict[str, Any]] = []
            total_confidence = 0.0
            confident_mappings = 0
            for column, suggestion in suggestions.items():
                field = suggestion.get("field", "")
                confidence = suggestion.get("confidence", 0.0)
                status = (
                    "🟢 High"
                    if confidence >= 0.7
                    else "🟡 Medium" if confidence >= 0.4 else "🔴 Low"
                )
                try:
                    sample_data = df[column].dropna().head(3).astype(str).tolist()
                except Exception:  # pragma: no cover - best effort
                    sample_data = ["N/A"]
                processed_suggestions.append(
                    {
                        "column": column,
                        "suggested_field": field if field else "No suggestion",
                        "confidence": confidence,
                        "status": status,
                        "sample_data": sample_data,
                    }
                )
                total_confidence += confidence
                if confidence >= 0.6:
                    confident_mappings += 1

            avg_confidence = total_confidence / len(suggestions) if suggestions else 0
            try:
                data_preview = serialize_dataframe_preview(df)
            except Exception:  # pragma: no cover - best effort
                data_preview = []

            return {
                "filename": filename,
                "total_columns": len(df.columns),
                "total_rows": len(df),
                "suggestions": processed_suggestions,
                "avg_confidence": avg_confidence,
                "confident_mappings": confident_mappings,
                "data_preview": data_preview,
                "column_names": list(df.columns),
            }
        else:
            return {
                "error": (
                    f"Suggests analysis not available for data source: "
                    f"{data_source}"
                )
            }
    except Exception as exc:  # pragma: no cover - best effort
        logger.exception("Failed to process suggests: %s", exc)
        return {"error": f"Failed to process suggests: {str(exc)}"}


@lru_cache(maxsize=32)
def process_quality_analysis(data_source: str) -> Dict[str, Any]:
    """Perform basic data quality analysis."""
    try:
        if data_source.startswith("upload:") or data_source == "service:uploaded":
            if data_source.startswith("upload:"):
                filename = data_source.replace("upload:", "")
            else:
                filename = None

            from yosai_intel_dashboard.src.services.upload_data_service import get_uploaded_data  # lazy import

            uploaded_files = get_uploaded_data()
            if not uploaded_files:
                return {"error": "No uploaded files found"}
            if filename is None or filename not in uploaded_files:
                filename = list(uploaded_files.keys())[0]

            df = uploaded_files[filename]

            total_rows = len(df)
            total_cols = len(df.columns)
            missing_values = df.isnull().sum().sum()
            duplicate_rows = df.duplicated().sum()
            quality_score = max(
                0,
                100
                - (missing_values / (total_rows * total_cols) * 100)
                - (duplicate_rows / total_rows * 10),
            )
            return {
                "analysis_type": "Data Quality",
                "data_source": data_source,
                "total_events": total_rows,
                "unique_users": 0,
                "unique_doors": 0,
                "success_rate": quality_score / 100,
                "analysis_focus": "Data completeness and duplication checks",
                "total_rows": total_rows,
                "total_columns": total_cols,
                "missing_values": missing_values,
                "duplicate_rows": duplicate_rows,
                "quality_score": quality_score,
            }
        return {"error": "Data quality analysis only available for uploaded files"}
    except Exception as exc:  # pragma: no cover - best effort
        logger.exception("Quality analysis processing error: %s", exc)
        return {"error": f"Quality analysis error: {str(exc)}"}


@lru_cache(maxsize=32)
def analyze_data_with_service(data_source: str, analysis_type: str) -> Dict[str, Any]:
    """Run analysis using the analytics service with chunked processing."""
    try:
        service = get_analytics_service()
        if not service:
            return {"error": "Analytics service not available"}

        if data_source.startswith("upload:") or data_source == "service:uploaded":
            from yosai_intel_dashboard.src.services.upload_data_service import get_uploaded_data  # lazy import

            uploaded_files = get_uploaded_data()
            if not uploaded_files:
                return {"error": "No uploaded files found"}
            if data_source.startswith("upload:"):
                filename = data_source.replace("upload:", "")
            else:
                filename = list(uploaded_files.keys())[0]
            df = uploaded_files.get(filename)
            if df is None:
                return {"error": f"File {filename} not found"}
        else:
            df, _ = service.processor.get_processed_database()
            if df.empty:
                return {"error": "No data available"}

        analysis_types = [analysis_type]
        results = service.analyze_with_chunking(df, analysis_types)
        return results
    except Exception as exc:  # pragma: no cover - best effort
        logger.exception("Analysis failed: %s", exc)
        return {"error": f"Analysis failed: {str(exc)}"}


# ---------------------------------------------------------------------------
# Simplified safe wrappers used in callbacks
# ---------------------------------------------------------------------------


def process_suggests_analysis_safe(data_source: str) -> Dict[str, Any]:
    """Safer variant of :func:`process_suggests_analysis`."""
    return process_suggests_analysis(data_source)


def process_quality_analysis_safe(data_source: str) -> Dict[str, Any]:
    """Safer variant of :func:`process_quality_analysis`."""
    return process_quality_analysis(data_source)


def analyze_data_with_service_safe(
    data_source: str, analysis_type: str
) -> Dict[str, Any]:
    """Safer variant of :func:`analyze_data_with_service`."""
    return analyze_data_with_service(data_source, analysis_type)


__all__ = [
    "get_data_source_options_safe",
    "get_latest_uploaded_source_value",
    "get_analysis_type_options",
    "clean_analysis_data_unicode",
    "get_ai_suggestions_for_file",
    "process_suggests_analysis",
    "process_quality_analysis",
    "analyze_data_with_service",
    "process_suggests_analysis_safe",
    "process_quality_analysis_safe",
    "analyze_data_with_service_safe",
]
