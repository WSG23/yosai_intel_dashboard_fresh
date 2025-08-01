# controllers/compliance_controller.py
"""Compliance API endpoints for GDPR/APPI"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from yosai_intel_dashboard.src.core.audit_logger import ComplianceAuditLogger
from yosai_intel_dashboard.src.core.container import Container
from yosai_intel_dashboard.src.core.rbac import require_role
from database.secure_exec import execute_query
from yosai_intel_dashboard.src.error_handling import ErrorCategory, ErrorHandler
from yosai_intel_dashboard.src.services.compliance.consent_service import ConsentService
from yosai_intel_dashboard.src.services.compliance.dsar_service import DSARService
from yosai_intel_dashboard.src.services.security import require_role
from shared.errors.types import ErrorCode
from validation.security_validator import SecurityValidator
from yosai_framework.errors import CODE_TO_STATUS
from yosai_intel_dashboard.models.compliance import ConsentType, DSARRequestType

logger = logging.getLogger(__name__)

# Create blueprint for compliance endpoints
compliance_bp = Blueprint("compliance", __name__, url_prefix="/v1/compliance")

handler = ErrorHandler()


def _parse_int_param(param_name: str, default: int) -> int:
    """Return sanitized integer query param or *default* if invalid."""
    value = request.args.get(param_name)
    if value is None:
        return default

    validator = SecurityValidator()
    result = validator.validate_input(str(value), param_name)
    sanitized = str(result.get("sanitized", value))
    return int(sanitized) if sanitized.isdigit() else default


def get_services() -> tuple[ConsentService, DSARService, ComplianceAuditLogger]:
    """Get compliance services from DI container"""
    container = Container()
    return (
        container.get("consent_service"),
        container.get("dsar_service"),
        container.get("audit_logger"),
    )


@compliance_bp.route("/consent", methods=["POST"])
@login_required
def grant_consent():
    """
    Grant consent for data processing
    ---
    post:
      description: Grant user consent for specific data processing activities
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [consent_type, jurisdiction]
              properties:
                consent_type:
                  type: string
                  enum: [biometric_access, security_analytics, facial_recognition, location_tracking, behavioral_analysis]
                jurisdiction:
                  type: string
                  enum: [EU, JP, US]
                  default: EU
      responses:
        200:
          description: Consent granted successfully
        400:
          description: Invalid request data
        500:
          description: Server error
    """
    try:
        data = request.get_json()
        validator = SecurityValidator()

        # Validate input
        if not data or not validator.validate_input(str(data), "json_data"):
            return jsonify({"error": "Invalid request data"}), 400

        consent_type_str = data.get("consent_type")
        jurisdiction = data.get("jurisdiction", "EU")

        if not consent_type_str:
            return jsonify({"error": "consent_type is required"}), 400

        try:
            consent_type = ConsentType(consent_type_str)
        except ValueError:
            return jsonify({"error": f"Invalid consent_type: {consent_type_str}"}), 400

        if jurisdiction not in ["EU", "JP", "US"]:
            return jsonify({"error": f"Invalid jurisdiction: {jurisdiction}"}), 400

        # Get services
        consent_service, _, audit_logger = get_services()

        # Grant consent
        success = consent_service.grant_consent(
            user_id=current_user.id,
            consent_type=consent_type,
            jurisdiction=jurisdiction,
            ip_address=request.remote_addr,
            user_agent=request.headers.get("User-Agent"),
        )

        if success:
            return (
                jsonify(
                    {
                        "message": f"Consent granted for {consent_type_str}",
                        "consent_type": consent_type_str,
                        "jurisdiction": jurisdiction,
                        "granted_at": datetime.now(timezone.utc).isoformat(),
                    }
                ),
                200,
            )
        else:
            return jsonify({"error": "Failed to grant consent"}), 500

    except Exception as e:
        logger.error(f"Error granting consent: {e}")
        err = handler.handle(e, ErrorCategory.INTERNAL)
        return jsonify(err.to_dict()), CODE_TO_STATUS[ErrorCode.INTERNAL]


@compliance_bp.route("/consent/<consent_type>", methods=["DELETE"])
@login_required
def withdraw_consent(consent_type: str):
    """
    Withdraw consent for data processing
    ---
    delete:
      description: Withdraw user consent for specific data processing activities
      parameters:
        - name: consent_type
          in: path
          required: true
          schema:
            type: string
        - name: jurisdiction
          in: query
          schema:
            type: string
            default: EU
      responses:
        200:
          description: Consent withdrawn successfully
        400:
          description: Invalid consent type
        404:
          description: No active consent found
    """
    try:
        jurisdiction = request.args.get("jurisdiction", "EU")

        try:
            consent_type_enum = ConsentType(consent_type)
        except ValueError:
            return jsonify({"error": f"Invalid consent_type: {consent_type}"}), 400

        # Get services
        consent_service, _, audit_logger = get_services()

        # Withdraw consent
        success = consent_service.withdraw_consent(
            user_id=current_user.id,
            consent_type=consent_type_enum,
            jurisdiction=jurisdiction,
        )

        if success:
            return (
                jsonify(
                    {
                        "message": f"Consent withdrawn for {consent_type}",
                        "consent_type": consent_type,
                        "jurisdiction": jurisdiction,
                        "withdrawn_at": datetime.now(timezone.utc).isoformat(),
                    }
                ),
                200,
            )
        else:
            return jsonify({"error": "No active consent found to withdraw"}), 404

    except Exception as e:
        logger.error(f"Error withdrawing consent: {e}")
        err = handler.handle(e, ErrorCategory.INTERNAL)
        return jsonify(err.to_dict()), CODE_TO_STATUS[ErrorCode.INTERNAL]


@compliance_bp.route("/consent/status", methods=["GET"])
@login_required
def get_consent_status():
    """
    Get user's current consent status
    ---
    get:
      description: Get all active consents for the current user
      parameters:
        - name: jurisdiction
          in: query
          schema:
            type: string
            default: EU
      responses:
        200:
          description: Consent status retrieved
          content:
            application/json:
              schema:
                type: object
                properties:
                  user_id:
                    type: string
                  jurisdiction:
                    type: string
                  consents:
                    type: array
                    items:
                      type: object
    """
    try:
        jurisdiction = request.args.get("jurisdiction", "EU")

        # Get services
        consent_service, _, _ = get_services()

        # Get all user consents
        consents = consent_service.get_user_consents(current_user.id)

        # Filter by jurisdiction and active status
        active_consents = [
            consent
            for consent in consents
            if consent.get("jurisdiction") == jurisdiction
            and consent.get("is_active", False)
        ]

        return (
            jsonify(
                {
                    "user_id": current_user.id,
                    "jurisdiction": jurisdiction,
                    "consents": active_consents,
                    "retrieved_at": datetime.now(timezone.utc).isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error getting consent status: {e}")
        err = handler.handle(e, ErrorCategory.INTERNAL)
        return jsonify(err.to_dict()), CODE_TO_STATUS[ErrorCode.INTERNAL]


@compliance_bp.route("/dsar/request", methods=["POST"])
@login_required
def create_dsar_request():
    """
    Create Data Subject Access Request
    ---
    post:
      description: Create a new DSAR (Data Subject Access Request)
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [request_type, email]
              properties:
                request_type:
                  type: string
                  enum: [access, portability, rectification, erasure, restriction]
                email:
                  type: string
                  format: email
                jurisdiction:
                  type: string
                  enum: [EU, JP, US]
                  default: EU
                details:
                  type: object
                  description: Additional request details
      responses:
        201:
          description: DSAR request created
        400:
          description: Invalid request data
    """
    try:
        data = request.get_json()
        validator = SecurityValidator()

        # Validate input
        if not data or not validator.validate_input(str(data), "json_data"):
            return jsonify({"error": "Invalid request data"}), 400

        request_type_str = data.get("request_type")
        email = data.get("email")
        jurisdiction = data.get("jurisdiction", "EU")
        details = data.get("details", {})

        if not request_type_str or not email:
            return jsonify({"error": "request_type and email are required"}), 400

        # Validate email format
        if not validator.validate_input(email, "email"):
            return jsonify({"error": "Invalid email format"}), 400

        try:
            request_type = DSARRequestType(request_type_str)
        except ValueError:
            return jsonify({"error": f"Invalid request_type: {request_type_str}"}), 400

        # Get services
        _, dsar_service, audit_logger = get_services()

        # Create DSAR request
        request_id = dsar_service.create_request(
            user_id=current_user.id,
            request_type=request_type,
            requestor_email=email,
            jurisdiction=jurisdiction,
            request_details=details,
        )

        return (
            jsonify(
                {
                    "request_id": request_id,
                    "request_type": request_type_str,
                    "status": "pending",
                    "jurisdiction": jurisdiction,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "message": f"DSAR request created. You will receive a response within 30 days.",
                }
            ),
            201,
        )

    except Exception as e:
        logger.error(f"Error creating DSAR request: {e}")
        err = handler.handle(e, ErrorCategory.INTERNAL)
        return jsonify(err.to_dict()), CODE_TO_STATUS[ErrorCode.INTERNAL]


@compliance_bp.route("/dsar/requests", methods=["GET"])
@login_required
def get_user_dsar_requests():
    """
    Get user's DSAR requests
    ---
    get:
      description: Get all DSAR requests for the current user
      responses:
        200:
          description: DSAR requests retrieved
    """
    try:
        # Get database connection through container
        container = Container()
        db = container.get("database")

        query_sql = """
            SELECT request_id, request_type, status, jurisdiction, received_date,
                   due_date, fulfilled_date, requestor_email
            FROM dsar_requests
            WHERE user_id = %s
            ORDER BY received_date DESC
        """

        df = execute_query(db, query_sql, (current_user.id,))
        requests = df.to_dict("records") if not df.empty else []

        return (
            jsonify(
                {
                    "user_id": current_user.id,
                    "requests": requests,
                    "retrieved_at": datetime.now(timezone.utc).isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error getting DSAR requests: {e}")
        err = handler.handle(e, ErrorCategory.INTERNAL)
        return jsonify(err.to_dict()), CODE_TO_STATUS[ErrorCode.INTERNAL]


@compliance_bp.route("/admin/dsar/pending", methods=["GET"])
@login_required
@require_role("admin")
def get_pending_dsar_requests():
    """
    Get pending DSAR requests (admin only)
    ---
    get:
      description: Get all pending DSAR requests for administrative processing
      parameters:
        - name: due_within_days
          in: query
          schema:
            type: integer
            default: 7
      responses:
        200:
          description: Pending DSAR requests retrieved
    """
    try:
        due_within_days = _parse_int_param("due_within_days", 7)

        # Get services
        _, dsar_service, audit_logger = get_services()

        pending_requests = dsar_service.get_pending_requests(due_within_days)

        # Log admin access to pending requests
        audit_logger.log_action(
            actor_user_id=current_user.id,
            action_type="VIEW_PENDING_DSAR_REQUESTS",
            resource_type="dsar_request",
            description=f"Accessed pending DSAR requests (due within {due_within_days} days)",
            legal_basis="administrative_obligation",
        )

        return (
            jsonify(
                {
                    "pending_requests": pending_requests,
                    "due_within_days": due_within_days,
                    "retrieved_at": datetime.now(timezone.utc).isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error getting pending DSAR requests: {e}")
        err = handler.handle(e, ErrorCategory.INTERNAL)
        return jsonify(err.to_dict()), CODE_TO_STATUS[ErrorCode.INTERNAL]


@compliance_bp.route("/admin/dsar/<request_id>/process", methods=["POST"])
@login_required
@require_role("admin")
def process_dsar_request(request_id: str):
    """
    Process a DSAR request (admin only)
    ---
    post:
      description: Process a pending DSAR request
      parameters:
        - name: request_id
          in: path
          required: true
          schema:
            type: string
      responses:
        200:
          description: DSAR request processed successfully
        404:
          description: Request not found
        400:
          description: Request cannot be processed
    """
    try:
        validator = SecurityValidator()

        # Validate request ID format
        if not validator.validate_input(request_id, "alphanumeric"):
            return jsonify({"error": "Invalid request ID format"}), 400

        # Get services
        _, dsar_service, audit_logger = get_services()

        # Process the request
        success = dsar_service.process_request(request_id, current_user.id)

        if success:
            return (
                jsonify(
                    {
                        "request_id": request_id,
                        "message": "DSAR request processed successfully",
                        "processed_by": current_user.id,
                        "processed_at": datetime.now(timezone.utc).isoformat(),
                    }
                ),
                200,
            )
        else:
            return jsonify({"error": "Failed to process DSAR request"}), 400

    except Exception as e:
        logger.error(f"Error processing DSAR request {request_id}: {e}")
        err = handler.handle(e, ErrorCategory.INTERNAL)
        return jsonify(err.to_dict()), CODE_TO_STATUS[ErrorCode.INTERNAL]


@compliance_bp.route("/audit/my-data", methods=["GET"])
@login_required
def get_my_audit_trail():
    """
    Get user's personal audit trail
    ---
    get:
      description: Get audit trail for current user's data
      parameters:
        - name: days
          in: query
          schema:
            type: integer
            default: 30
            minimum: 1
            maximum: 365
      responses:
        200:
          description: Audit trail retrieved
    """
    try:
        days = _parse_int_param("days", 30)
        if days < 1 or days > 365:
            return jsonify({"error": "Days must be between 1 and 365"}), 400

        # Get services
        _, _, audit_logger = get_services()

        audit_trail = audit_logger.get_user_audit_trail(current_user.id, days)

        return (
            jsonify(
                {
                    "user_id": current_user.id,
                    "audit_trail": audit_trail,
                    "period_days": days,
                    "retrieved_at": datetime.now(timezone.utc).isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error getting audit trail: {e}")
        err = handler.handle(e, ErrorCategory.INTERNAL)
        return jsonify(err.to_dict()), CODE_TO_STATUS[ErrorCode.INTERNAL]


@compliance_bp.route("/admin/compliance-report", methods=["GET"])
@login_required
@require_role("admin")
def generate_compliance_report():
    """
    Generate compliance report (admin only)
    ---
    get:
      description: Generate compliance report for regulators
      parameters:
        - name: start_date
          in: query
          schema:
            type: string
            format: date
        - name: end_date
          in: query
          schema:
            type: string
            format: date
      responses:
        200:
          description: Compliance report generated
    """
    try:
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")

        # Default to last 30 days if no dates provided
        if not start_date_str or not end_date_str:
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=30)
        else:
            try:
                start_date = datetime.fromisoformat(start_date_str).replace(
                    tzinfo=timezone.utc
                )
                end_date = datetime.fromisoformat(end_date_str).replace(
                    tzinfo=timezone.utc
                )
            except ValueError:
                return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

        # Get services
        _, _, audit_logger = get_services()

        # Generate report
        report = audit_logger.generate_compliance_report(start_date, end_date)

        # Log report generation
        audit_logger.log_action(
            actor_user_id=current_user.id,
            action_type="GENERATE_COMPLIANCE_REPORT",
            resource_type="compliance_report",
            description=f"Generated compliance report for {start_date.date()} to {end_date.date()}",
            legal_basis="regulatory_compliance",
        )

        return jsonify(report), 200

    except Exception as e:
        logger.error(f"Error generating compliance report: {e}")
        err = handler.handle(e, ErrorCategory.INTERNAL)
        return jsonify(err.to_dict()), CODE_TO_STATUS[ErrorCode.INTERNAL]


@compliance_bp.route("/health", methods=["GET"])
def compliance_health_check():
    """
    Health check for compliance services
    ---
    get:
      description: Check if compliance services are operational
      responses:
        200:
          description: Services are healthy
        503:
          description: Services are unhealthy
    """
    try:
        # Test database connectivity
        container = Container()
        db = container.get("database")

        # Simple query to test database
        test_query = "SELECT 1 as health_check"
        result = execute_query(db, test_query)

        if result.empty:
            return (
                jsonify({"status": "unhealthy", "error": "Database test failed"}),
                503,
            )

        return (
            jsonify(
                {
                    "status": "healthy",
                    "services": ["consent_service", "dsar_service", "audit_logger"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Compliance health check failed: {e}")
        err = handler.handle(e, ErrorCategory.INTERNAL)
        return jsonify(err.to_dict()), CODE_TO_STATUS[ErrorCode.INTERNAL]


# Error handlers
@compliance_bp.errorhandler(400)
def bad_request(error):
    err = handler.handle(error, ErrorCategory.INVALID_INPUT)
    return jsonify(err.to_dict()), CODE_TO_STATUS[ErrorCode.INVALID_INPUT]


@compliance_bp.errorhandler(403)
def forbidden(error):
    err = handler.handle(error, ErrorCategory.UNAUTHORIZED)
    return jsonify(err.to_dict()), CODE_TO_STATUS[ErrorCode.UNAUTHORIZED]


@compliance_bp.errorhandler(404)
def not_found(error):
    err = handler.handle(error, ErrorCategory.NOT_FOUND)
    return jsonify(err.to_dict()), CODE_TO_STATUS[ErrorCode.NOT_FOUND]


@compliance_bp.errorhandler(500)
def internal_error(error):
    err = handler.handle(error, ErrorCategory.INTERNAL)
    return jsonify(err.to_dict()), CODE_TO_STATUS[ErrorCode.INTERNAL]


# Register blueprint function
def register_compliance_routes(app):
    """Register compliance routes with Flask app"""
    app.register_blueprint(compliance_bp)
