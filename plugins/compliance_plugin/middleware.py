#!/usr/bin/env python3
"""
Compliance Middleware
Provides automatic audit logging and compliance checks for Flask requests
"""

from __future__ import annotations

import logging
import time
from functools import wraps
from typing import Any, Dict, Optional

from flask import g, request

from core.error_handling import ErrorSeverity, error_handler, handle_errors

logger = logging.getLogger(__name__)


class ComplianceMiddleware:
    """
    Flask middleware for automatic compliance operations
    """

    def __init__(self, container, config):
        """
        Initialize compliance middleware

        Args:
            container: Dependency injection container
            config: Compliance configuration
        """
        self.container = container
        self.config = config
        self.audit_logger = None
        self.consent_service = None

    def register_middleware(self, app) -> bool:
        """
        Register middleware with Flask app

        Args:
            app: Flask application instance

        Returns:
            bool: True if middleware registered successfully
        """
        try:
            # Get services from container
            self.audit_logger = self.container.get("compliance_audit_logger")
            self.consent_service = self.container.get("compliance_consent_service")

            # Register request hooks
            app.before_request(self._before_request)
            app.after_request(self._after_request)
            app.teardown_request(self._teardown_request)

            logger.info("Compliance middleware registered successfully")
            return True

        except Exception as e:
            error_handler.handle_error(
                e,
                severity=ErrorSeverity.HIGH,
                context={
                    "service": "compliance_middleware",
                    "operation": "register_middleware",
                },
            )
            return False

    @handle_errors(
        service="compliance_middleware",
        operation="before_request",
        severity=ErrorSeverity.HIGH,
    )
    def _before_request(self):
        """
        Called before each request
        Sets up request context and performs pre-request compliance checks
        """
        # Store request start time
        g.request_start_time = time.time()

        # Generate request ID for tracing
        import uuid

        g.request_id = str(uuid.uuid4())

        # Skip compliance checks for certain paths
        if self._should_skip_compliance():
            return

        # Log request start if audit logging is enabled
        if self.audit_logger and self.config.audit_enabled:
            self._log_request_start()

    @handle_errors(
        service="compliance_middleware",
        operation="after_request",
        severity=ErrorSeverity.HIGH,
    )
    def _after_request(self, response):
        """
        Called after each request
        Performs post-request compliance operations
        """
        # Skip compliance operations for certain paths
        if self._should_skip_compliance():
            return response

        # Add compliance headers
        self._add_compliance_headers(response)

        return response

    @handle_errors(
        service="compliance_middleware",
        operation="teardown_request",
        severity=ErrorSeverity.HIGH,
    )
    def _teardown_request(self, exception):
        """
        Called during request teardown
        Performs cleanup and error logging
        """
        if exception and self.audit_logger:
            logger.error(f"Request failed with exception: {exception}")

    def _should_skip_compliance(self) -> bool:
        """
        Determine if compliance operations should be skipped for this request

        Returns:
            bool: True if compliance should be skipped
        """
        # Skip for static files, health checks, etc.
        skip_paths = [
            "/static/",
            "/health",
            "/favicon.ico",
            "/_dash-",  # Dash internal endpoints
            "/assets/",
        ]

        path = request.path
        return any(skip_path in path for skip_path in skip_paths)

    @handle_errors(
        service="compliance_middleware",
        operation="log_request_start",
        severity=ErrorSeverity.HIGH,
    )
    def _log_request_start(self):
        """Log the start of a request"""
        user_id = self._get_user_id_from_request()

        if self.audit_logger:
            self.audit_logger.log_action(
                actor_user_id=user_id or "anonymous",
                action_type="REQUEST_START",
                resource_type="api_endpoint",
                resource_id=request.endpoint,
                description=f"{request.method} {request.path}",
                ip_address=request.remote_addr,
                user_agent=request.headers.get("User-Agent"),
            )

    @handle_errors(
        service="compliance_middleware",
        operation="add_compliance_headers",
        severity=ErrorSeverity.HIGH,
    )
    def _add_compliance_headers(self, response):
        """
        Add compliance-related headers to response
        """
        # Add request ID for tracing
        if hasattr(g, "request_id"):
            response.headers["X-Request-ID"] = g.request_id

        # Add compliance headers
        response.headers["X-Compliance-Framework"] = "GDPR-APPI"
        response.headers["X-Data-Protection"] = "Enabled"

    @handle_errors(
        service="compliance_middleware",
        operation="get_user_id_from_request",
        severity=ErrorSeverity.MEDIUM,
    )
    def _get_user_id_from_request(self) -> Optional[str]:
        """
        Extract user ID from the current request

        Returns:
            str: User ID if available, None otherwise
        """
        # Try to get from custom header
        user_id = request.headers.get("X-User-ID")
        if user_id:
            return str(user_id)
        return None
