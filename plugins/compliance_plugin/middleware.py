#!/usr/bin/env python3
"""
Compliance Middleware
Provides automatic audit logging and compliance checks for Flask requests
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional
from flask import request, g
from functools import wraps

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
            self.audit_logger = self.container.get('compliance_audit_logger')
            self.consent_service = self.container.get('compliance_consent_service')
            
            # Register request hooks
            app.before_request(self._before_request)
            app.after_request(self._after_request)
            app.teardown_request(self._teardown_request)
            
            logger.info("Compliance middleware registered successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register compliance middleware: {e}")
            return False
    
    def _before_request(self):
        """
        Called before each request
        Sets up request context and performs pre-request compliance checks
        """
        try:
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
                
        except Exception as e:
            logger.error(f"Error in before_request middleware: {e}")
    
    def _after_request(self, response):
        """
        Called after each request
        Performs post-request compliance operations
        """
        try:
            # Skip compliance operations for certain paths
            if self._should_skip_compliance():
                return response
            
            # Add compliance headers
            self._add_compliance_headers(response)
            
        except Exception as e:
            logger.error(f"Error in after_request middleware: {e}")
        
        return response
    
    def _teardown_request(self, exception):
        """
        Called during request teardown
        Performs cleanup and error logging
        """
        try:
            if exception and self.audit_logger:
                logger.error(f"Request failed with exception: {exception}")
                
        except Exception as e:
            logger.error(f"Error in teardown_request middleware: {e}")
    
    def _should_skip_compliance(self) -> bool:
        """
        Determine if compliance operations should be skipped for this request
        
        Returns:
            bool: True if compliance should be skipped
        """
        # Skip for static files, health checks, etc.
        skip_paths = [
            '/static/',
            '/health',
            '/favicon.ico',
            '/_dash-',  # Dash internal endpoints
            '/assets/'
        ]
        
        path = request.path
        return any(skip_path in path for skip_path in skip_paths)
    
    def _log_request_start(self):
        """Log the start of a request"""
        try:
            user_id = self._get_user_id_from_request()
            
            if self.audit_logger:
                self.audit_logger.log_action(
                    actor_user_id=user_id or 'anonymous',
                    action_type='REQUEST_START',
                    resource_type='api_endpoint',
                    resource_id=request.endpoint,
                    description=f"{request.method} {request.path}",
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent')
                )
            
        except Exception as e:
            logger.error(f"Failed to log request start: {e}")
    
    def _add_compliance_headers(self, response):
        """
        Add compliance-related headers to response
        """
        try:
            # Add request ID for tracing
            if hasattr(g, 'request_id'):
                response.headers['X-Request-ID'] = g.request_id
            
            # Add compliance headers
            response.headers['X-Compliance-Framework'] = 'GDPR-APPI'
            response.headers['X-Data-Protection'] = 'Enabled'
                
        except Exception as e:
            logger.error(f"Failed to add compliance headers: {e}")
    
    def _get_user_id_from_request(self) -> Optional[str]:
        """
        Extract user ID from the current request
        
        Returns:
            str: User ID if available, None otherwise
        """
        try:
            # Try to get from custom header
            user_id = request.headers.get('X-User-ID')
            if user_id:
                return str(user_id)
                
        except Exception as e:
            logger.error(f"Failed to get user ID from request: {e}")
        
        return None
