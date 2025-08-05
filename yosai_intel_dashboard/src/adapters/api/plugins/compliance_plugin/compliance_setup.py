# config/compliance_setup.py
"""Compliance Framework Integration Setup"""

from __future__ import annotations

import logging
from typing import Any, Dict

from controllers.compliance_controller import register_compliance_routes

from yosai_intel_dashboard.models.compliance import CREATE_COMPLIANCE_TABLES_SQL
from yosai_intel_dashboard.src.core.audit_logger import create_audit_logger
from yosai_intel_dashboard.src.core.container import Container
from yosai_intel_dashboard.src.core.interfaces.protocols import DatabaseProtocol
from yosai_intel_dashboard.src.database.secure_exec import (
    execute_command,
    execute_query,
)
from yosai_intel_dashboard.src.services.compliance.consent_service import (
    create_consent_service,
)
from yosai_intel_dashboard.src.services.compliance.dsar_service import (
    create_dsar_service,
)

logger = logging.getLogger(__name__)


def setup_compliance_services(container: Container) -> None:
    """
    Register compliance services with DI container
    Call this from your app factory after database setup
    """
    try:
        # Get database from container
        db = container.get("database")

        # Create audit logger first (needed by other services)
        audit_logger = create_audit_logger(db)
        container.register("audit_logger", audit_logger)

        # Create consent service
        consent_service = create_consent_service(db, audit_logger)
        container.register("consent_service", consent_service)

        # Create DSAR service
        dsar_service = create_dsar_service(db, audit_logger)
        container.register("dsar_service", dsar_service)

        logger.info("Compliance services registered successfully")

    except Exception as e:
        logger.error(f"Failed to setup compliance services: {e}")
        raise


def ensure_compliance_schema(db: DatabaseProtocol) -> bool:
    """
    Create compliance tables if they don't exist
    Call this during application startup
    """
    try:
        # Execute the compliance table creation SQL
        execute_command(db, CREATE_COMPLIANCE_TABLES_SQL)
        logger.info("Compliance database schema ensured")
        return True

    except Exception as e:
        logger.error(f"Failed to create compliance schema: {e}")
        return False


def register_compliance_middleware(app) -> None:
    """
    Register compliance-related middleware and decorators
    """
    from functools import wraps
    from uuid import uuid4

    from flask import g, request

    @app.before_request
    def set_request_id():
        """Set unique request ID for audit tracing"""
        g.request_id = request.headers.get("X-Request-ID", str(uuid4())[:8].upper())

    @app.after_request
    def add_audit_headers(response):
        """Add audit-related headers to responses"""
        if hasattr(g, "request_id"):
            response.headers["X-Request-ID"] = g.request_id
        return response


def audit_decorator(action_type: str, resource_type: str):
    """
    Decorator to automatically audit sensitive operations

    Usage:
    @audit_decorator('VIEW_USER_PROFILE', 'user_profile')
    def get_user_profile(user_id):
        # Your function logic
        pass
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            from flask_login import current_user

            from yosai_intel_dashboard.src.core.container import Container

            try:
                # Execute the function first
                result = func(*args, **kwargs)

                # Then audit the successful operation
                container = Container()
                audit_logger = container.get("audit_logger")

                # Extract user_id from args/kwargs if available
                target_user_id = kwargs.get("user_id") or (args[0] if args else None)

                audit_logger.log_action(
                    actor_user_id=(
                        current_user.id if current_user.is_authenticated else "system"
                    ),
                    target_user_id=target_user_id,
                    action_type=action_type,
                    resource_type=resource_type,
                    description=f"Function {func.__name__} executed successfully",
                )

                return result

            except Exception as e:
                # Log failed operations too
                try:
                    container = Container()
                    audit_logger = container.get("audit_logger")
                    audit_logger.log_action(
                        actor_user_id=(
                            current_user.id
                            if current_user.is_authenticated
                            else "system"
                        ),
                        action_type=f"FAILED_{action_type}",
                        resource_type=resource_type,
                        description=f"Function {func.__name__} failed: {str(e)}",
                    )
                except:
                    pass  # Don't let audit logging break the original exception

                raise e

        return wrapper

    return decorator


def consent_required(consent_type: str, jurisdiction: str = "EU"):
    """
    Decorator to check consent before executing biometric operations

    Usage:
    @consent_required('facial_recognition', 'EU')
    def process_facial_recognition(user_id):
        # Your biometric processing logic
        pass
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            from flask import jsonify
            from flask_login import current_user

            from yosai_intel_dashboard.models.compliance import ConsentType
            from yosai_intel_dashboard.src.core.container import Container

            try:
                container = Container()
                consent_service = container.get("consent_service")

                # Check if consent exists
                consent_type_enum = ConsentType(consent_type)
                has_consent = consent_service.check_consent(
                    user_id=current_user.id,
                    consent_type=consent_type_enum,
                    jurisdiction=jurisdiction,
                )

                if not has_consent:
                    # Log the denied access
                    audit_logger = container.get("audit_logger")
                    audit_logger.log_action(
                        actor_user_id=current_user.id,
                        action_type="CONSENT_DENIED_ACCESS",
                        resource_type="biometric_operation",
                        description=f"Access denied - no consent for {consent_type}",
                        legal_basis="consent_required",
                    )

                    return (
                        jsonify(
                            {
                                "error": f"Consent required for {consent_type}",
                                "consent_type": consent_type,
                                "jurisdiction": jurisdiction,
                            }
                        ),
                        403,
                    )

                # Consent exists, proceed with operation
                return func(*args, **kwargs)

            except Exception as e:
                logger.error(f"Consent check failed: {e}")
                return jsonify({"error": "Consent verification failed"}), 500

        return wrapper

    return decorator


# Modified app factory integration example
def create_compliance_enabled_app(config_name: str = None):
    """
    Example of how to modify your existing app factory to include compliance

    Replace your existing create_app() function with this pattern:
    """
    from flask import Flask

    from yosai_intel_dashboard.src.core.container import Container
    from yosai_intel_dashboard.src.database.connection import create_database_connection
    from yosai_intel_dashboard.src.infrastructure.config import create_config_manager

    # Create Flask app
    app = Flask(__name__)

    # Load configuration
    config_manager = create_config_manager()
    app.config.update(config_manager.get_app_config().__dict__)

    # Create DI container
    container = Container()
    container.register("config", config_manager)

    # Setup database
    db = create_database_connection()
    container.register("database", db)

    # COMPLIANCE INTEGRATION - Add these lines to your existing app factory:

    # 1. Ensure compliance database schema exists
    if not ensure_compliance_schema(db):
        logger.warning("Failed to setup compliance database schema")

    # 2. Register compliance services
    setup_compliance_services(container)

    # 3. Register compliance middleware
    register_compliance_middleware(app)

    # 4. Register compliance API routes
    register_compliance_routes(app)

    # Register existing services (your current code)
    # ... your existing service registrations ...

    # Store container in app for access in views
    app.container = container

    return app


# Data retention automation (scheduled task)
def setup_data_retention_scheduler():
    """
    Setup automated data retention cleanup.

    Uses the :mod:`schedule` library to run ``cleanup_expired_data`` every day
    at 02:00, ensuring data is purged according to configured retention rules
    (e.g., "biometric_templates" retained 30 days per GDPR Art.5(1)(e)).

    A cron-based deployment could instead add an entry such as::

        0 2 * * * /usr/bin/python manage.py run_retention_cleanup

    Either approach enforces the legal bases defined for each data type and
    jurisdiction.
    """
    import time
    from threading import Thread

    import schedule

    def cleanup_expired_data():
        """Clean up data that has exceeded retention periods"""
        try:
            from datetime import datetime, timezone

            from yosai_intel_dashboard.src.core.container import Container

            container = Container()
            db = container.get("database")
            audit_logger = container.get("audit_logger")

            # Get expired data based on retention policies
            cleanup_sql = """
                SELECT p.person_id, p.data_retention_date
                FROM people p
                WHERE p.data_retention_date IS NOT NULL 
                  AND p.data_retention_date <= %s
            """

            now = datetime.now(timezone.utc)
            df = execute_query(db, cleanup_sql, (now,))

            for row in df.itertuples(index=False):
                person_id = row.person_id

                # Delete biometric data
                delete_biometric_sql = (
                    "DELETE FROM biometric_templates WHERE person_id = %s"
                )
                execute_command(db, delete_biometric_sql, (person_id,))

                # Clear retention date
                update_sql = (
                    "UPDATE people SET data_retention_date = NULL WHERE person_id = %s"
                )
                execute_command(db, update_sql, (person_id,))

                # Audit the deletion
                audit_logger.log_data_deletion(
                    actor_user_id="system",
                    target_user_id=person_id,
                    data_types=["biometric_templates"],
                    retention_policy="automated_cleanup",
                )

                logger.info(f"Automated data cleanup completed for user {person_id}")

        except Exception as e:
            logger.error(f"Data retention cleanup failed: {e}")

    # Schedule daily cleanup at 2 AM
    schedule.every().day.at("02:00").do(cleanup_expired_data)

    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(3600)  # Check every hour

    # Run scheduler in background thread
    scheduler_thread = Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

    logger.info("Data retention scheduler started")


# Example usage in your main application file
if __name__ == "__main__":
    # Replace your existing app creation with:
    app = create_compliance_enabled_app()

    # Optional: Start data retention scheduler
    setup_data_retention_scheduler()

    # Run the app
    app.run(debug=True)
