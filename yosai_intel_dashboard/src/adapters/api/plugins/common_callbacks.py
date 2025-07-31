from __future__ import annotations

from typing import Any, Dict


def csv_pre_process_callback(
    services: Any,
    file_path: str,
    upload_context: Dict[str, Any] | None,
    uploaded_by: str | None,
) -> Dict[str, Any]:
    """Run CSV compliance analysis and return standard callback response."""

    if not services or not getattr(services, "csv_processor", None):
        return {"status": "proceed"}

    result = services.csv_processor.analyze_csv_compliance(
        file_path,
        upload_context or {},
        uploaded_by,
    )

    if not result.get("authorized", True):
        return {
            "status": "block",
            "reason": result.get("reason", "Compliance check failed"),
            "details": result,
        }

    return {"status": "proceed", "compliance_metadata": result}


__all__ = ["csv_pre_process_callback"]
