#!/usr/bin/env python3
"""
Main Compliance Plugin Class - Extracted from __init__.py
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from yosai_intel_dashboard.src.core.plugins.base import BasePlugin
from plugins.common_callbacks import csv_pre_process_callback

from .api import ComplianceAPI
from .config import ComplianceConfig
from .database import ComplianceDatabase
from .middleware import ComplianceMiddleware
from .services import ComplianceServices

logger = logging.getLogger(__name__)


class CompliancePlugin(BasePlugin):
    """
    Main compliance plugin that provides GDPR/APPI compliance features
    as an optional add-on to the core application
    """

    def __init__(self):
        super().__init__()
        self.name = "compliance_plugin"
        self.version = "1.0.0"
        self.description = "GDPR/APPI compliance framework"
        self.author = "Yōsai Intel Compliance Team"
        self.dependencies = []  # No dependencies on other plugins

        # Plugin components
        self.services: Optional[ComplianceServices] = None
        self.api: Optional[ComplianceAPI] = None
        self.middleware: Optional[ComplianceMiddleware] = None
        self.database: Optional[ComplianceDatabase] = None
        self.config: Optional[ComplianceConfig] = None

        # Plugin state
        self.is_initialized = False
        self.is_database_ready = False

    def initialize(self, container: Container, config: Dict[str, Any]) -> bool:
        """Initialize the compliance plugin"""
        try:
            logger.info("Initializing Compliance Plugin v%s", self.version)

            # 1. Load plugin configuration
            self.config = ComplianceConfig(config.get("compliance", {}))

            if not self.config.enabled:
                logger.info("Compliance plugin is disabled in configuration")
                return True

            # 2. Initialize database components
            self.database = ComplianceDatabase(container.get("database"))
            if not self.database.ensure_schema():
                logger.error("Failed to initialize compliance database schema")
                return False
            self.is_database_ready = True

            # 3. Initialize services
            self.services = ComplianceServices(container, self.config)
            if not self.services.initialize():
                logger.error("Failed to initialize compliance services")
                return False

            # 4. Register services with DI container
            self._register_services_with_container(container)

            # 5. Initialize API endpoints
            self.api = ComplianceAPI(container, self.config)

            # 6. Initialize middleware
            self.middleware = ComplianceMiddleware(container, self.config)

            self.is_initialized = True
            logger.info("Compliance plugin initialized successfully")
            return True

        except Exception as e:
            logger.error("Failed to initialize compliance plugin: %s", e)
            return False

    def register_routes(self, app) -> bool:
        """Register compliance API routes with Flask app"""
        if not self.is_initialized or not self.api:
            logger.warning("Cannot register routes - plugin not initialized")
            return False

        try:
            # Register compliance API routes
            self.api.register_routes(app)

            # Register middleware
            if self.middleware:
                self.middleware.register_middleware(app)

            logger.info("Compliance plugin routes registered")
            return True

        except Exception as e:
            logger.error("Failed to register compliance routes: %s", e)
            return False

    def get_hooks(self) -> Dict[str, Any]:
        """Return hooks that integrate with core application workflows"""
        if not self.is_initialized:
            return {}

        return {
            # CSV processing hooks
            "csv_upload_pre_process": self._hook_csv_pre_process,
            "csv_upload_post_process": self._hook_csv_post_process,
            "csv_data_access": self._hook_csv_data_access,
            "csv_data_deletion": self._hook_csv_data_deletion,
            # User management hooks
            "user_registration": self._hook_user_registration,
            "user_deletion": self._hook_user_deletion,
            "user_data_export": self._hook_user_data_export,
            # Biometric processing hooks
            "biometric_processing_pre": self._hook_biometric_pre_process,
            "biometric_processing_post": self._hook_biometric_post_process,
            # Analytics hooks
            "analytics_access_request": self._hook_analytics_access_request,
            "analytics_processing": self._hook_analytics_processing,
            # System hooks
            "daily_maintenance": self._hook_daily_maintenance,
            "health_check": self._hook_health_check,
        }

    def get_dashboard_widgets(self) -> List[Dict[str, Any]]:
        """Return dashboard widgets for compliance monitoring"""
        if not self.is_initialized or not self.services:
            return []

        return [
            {
                "id": "compliance_score",
                "title": "Compliance Score",
                "type": "metric_card",
                "component": "ComplianceScoreWidget",
                "data_source": "/api/v1/compliance/dashboard/score",
                "refresh_interval": 300,  # 5 minutes
            },
            {
                "id": "consent_status",
                "title": "Consent Management",
                "type": "chart",
                "component": "ConsentStatusChart",
                "data_source": "/api/v1/compliance/dashboard/consent",
                "refresh_interval": 600,  # 10 minutes
            },
            {
                "id": "dsar_queue",
                "title": "DSAR Requests",
                "type": "table",
                "component": "DSARQueueTable",
                "data_source": "/api/v1/compliance/dashboard/dsar",
                "refresh_interval": 300,
            },
            {
                "id": "compliance_alerts",
                "title": "Compliance Alerts",
                "type": "alert_list",
                "component": "ComplianceAlerts",
                "data_source": "/api/v1/compliance/dashboard/alerts",
                "refresh_interval": 60,  # 1 minute
            },
        ]

    def shutdown(self) -> bool:
        """Shutdown the compliance plugin"""
        try:
            logger.info("Shutting down compliance plugin")

            # Stop background services
            if self.services:
                self.services.shutdown()

            # Clean up resources
            self.is_initialized = False
            logger.info("Compliance plugin shutdown complete")
            return True

        except Exception as e:
            logger.error("Error during compliance plugin shutdown: %s", e)
            return False

    def get_plugin_info(self) -> Dict[str, Any]:
        """Return plugin information for admin interface"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "status": "active" if self.is_initialized else "inactive",
            "database_ready": self.is_database_ready,
            "features": [
                "Consent Management",
                "Data Subject Rights (DSAR)",
                "Audit Logging",
                "Data Retention",
                "Breach Notification",
                "Cross-Border Transfers",
                "DPIA Automation",
                "Compliance Dashboard",
            ],
            "configuration": self.config.to_dict() if self.config else {},
            "health_status": self._get_health_status(),
        }

    # Hook implementations
    def _hook_csv_pre_process(self, **kwargs) -> Dict[str, Any]:
        """Hook called before CSV processing"""
        file_path = kwargs.get("file_path")
        upload_context = kwargs.get("upload_context")
        uploaded_by = kwargs.get("uploaded_by")

        return csv_pre_process_callback(
            self.services,
            file_path,
            upload_context,
            uploaded_by,
        )

    def _hook_csv_post_process(self, **kwargs) -> Dict[str, Any]:
        """Hook called after CSV processing"""
        if not self.services:
            return {}

        # Apply retention policies and audit logging
        processing_id = kwargs.get("processing_id")
        compliance_metadata = kwargs.get("compliance_metadata", {})

        if processing_id and compliance_metadata:
            self.services.retention_service.apply_csv_retention_policy(
                processing_id, compliance_metadata
            )

        return {}

    def _hook_biometric_pre_process(self, **kwargs) -> Dict[str, Any]:
        """Hook called before biometric processing"""
        if not self.services or not self.services.consent_service:
            return {"status": "proceed"}

        user_id = kwargs.get("user_id")
        processing_type = kwargs.get("processing_type", "biometric_access")

        # Check consent
        from .models import ConsentType

        consent_type = (
            ConsentType.FACIAL_RECOGNITION
            if "facial" in processing_type
            else ConsentType.BIOMETRIC_ACCESS
        )

        has_consent = self.services.consent_service.check_consent(
            user_id=user_id, consent_type=consent_type, jurisdiction="EU"
        )

        if not has_consent:
            return {
                "status": "block",
                "reason": f"No consent for {processing_type}",
                "consent_required": consent_type.value,
            }

        return {"status": "proceed"}

    def _hook_daily_maintenance(self, **kwargs) -> Dict[str, Any]:
        """Hook called during daily maintenance"""
        if not self.services:
            return {}

        # Run automated data retention
        if self.services.retention_service:
            deleted_count = (
                self.services.retention_service.process_scheduled_deletions()
            )
            logger.info(
                "Compliance maintenance: processed %d scheduled deletions",
                deleted_count,
            )

        return {"deleted_records": deleted_count if "deleted_count" in locals() else 0}

    def _register_services_with_container(self, container: Container) -> None:
        """Register compliance services with the DI container"""
        if not self.services:
            return

        # Register all compliance services
        container.register("compliance_audit_logger", self.services.audit_logger)
        container.register("compliance_consent_service", self.services.consent_service)
        container.register("compliance_dsar_service", self.services.dsar_service)
        container.register(
            "compliance_retention_service", self.services.retention_service
        )
        container.register("compliance_dpia_service", self.services.dpia_service)
        container.register("compliance_dashboard", self.services.dashboard)
        container.register("compliance_csv_processor", self.services.csv_processor)

        # Register plugin itself for access to hooks
        container.register("compliance_plugin", self)

    def _get_health_status(self) -> Dict[str, Any]:
        """Get health status of compliance plugin"""
        if not self.is_initialized:
            return {"status": "inactive", "issues": ["Plugin not initialized"]}

        issues = []

        # Check database connectivity
        if not self.is_database_ready:
            issues.append("Database schema not ready")

        # Check services
        if not self.services or not self.services.is_healthy():
            issues.append("Services not healthy")

        return {
            "status": "healthy" if not issues else "degraded",
            "issues": issues,
            "last_check": self._get_current_timestamp(),
        }
