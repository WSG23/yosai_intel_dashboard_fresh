#!/usr/bin/env python3
"""
Compliance Database Manager
Handles database schema creation and migrations for compliance plugin
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from database.secure_exec import execute_command, execute_query

logger = logging.getLogger(__name__)


class ComplianceDatabase:
    """
    Database manager for compliance plugin
    Handles schema creation, migrations, and database operations
    """

    def __init__(self, db_connection):
        """
        Initialize compliance database manager

        Args:
            db_connection: Database connection from DI container
        """
        self.db = db_connection
        self.schema_version = "1.0.0"

    def ensure_schema(self) -> bool:
        """
        Ensure compliance database schema exists

        Returns:
            bool: True if schema was created/verified successfully
        """
        try:
            # Check if we have the SQL from yosai_intel_dashboard.src.core.domain file or schema file
            schema_sql = self._get_schema_sql()

            if schema_sql:
                # Execute the schema creation SQL
                if hasattr(self.db, "execute_command"):
                    execute_command(self.db, schema_sql)
                else:
                    self.db.execute(schema_sql)
                    self.db.commit()

                logger.info("Compliance database schema ensured")
                return True
            else:
                logger.warning("No schema SQL found - using existing tables")
                return True

        except Exception as e:
            logger.error(f"Failed to ensure compliance database schema: {e}")
            return False

    def _get_schema_sql(self) -> Optional[str]:
        """
        Get the schema SQL from the models file or external SQL file

        Returns:
            str: SQL schema creation statements
        """
        try:
            # First try to get SQL from yosai_intel_dashboard.src.core.domain file
            from .models.compliance import CREATE_COMPLIANCE_TABLES_SQL

            return CREATE_COMPLIANCE_TABLES_SQL
        except ImportError:
            logger.warning("Could not import CREATE_COMPLIANCE_TABLES_SQL from models")

        # Fallback: try to read from database/schema.sql file
        schema_path = Path(__file__).parent / "database" / "schema.sql"
        if schema_path.exists():
            try:
                with open(schema_path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Failed to read schema file {schema_path}: {e}")

        return None

    def validate_schema(self) -> Dict[str, Any]:
        """
        Validate that all required tables exist and have correct structure

        Returns:
            Dict containing validation results
        """
        required_tables = [
            "consent_log",
            "dsar_requests",
            "compliance_audit_log",
            "data_retention_policies",
        ]

        results = {"valid": True, "missing_tables": [], "table_status": {}}

        for table in required_tables:
            try:
                # Try to query table structure
                sql = f"SELECT 1 FROM {table} LIMIT 1"

                if hasattr(self.db, "execute_query"):
                    execute_query(self.db, sql)
                else:
                    cursor = execute_command(self.db, sql)
                    cursor.fetchone()

                results["table_status"][table] = "exists"

            except Exception as e:
                results["missing_tables"].append(table)
                results["table_status"][table] = f"missing: {str(e)}"
                results["valid"] = False

        return results
