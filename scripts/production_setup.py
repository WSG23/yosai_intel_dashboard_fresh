import os
from pathlib import Path

from config import ConfigManager
from yosai_intel_dashboard.src.core.secrets_validator import validate_all_secrets
from database.connection import create_database_connection
from database.secure_exec import execute_command


def validate_environment() -> ConfigManager:
    """Validate required environment variables and secrets."""
    validate_all_secrets()
    config = ConfigManager()
    return config


def ensure_ssl_certificates(
    cert_file: str | None = None, key_file: str | None = None
) -> None:
    """Ensure SSL certificate files exist.

    By default this reads ``SSL_CERT_PATH`` and ``SSL_KEY_PATH`` environment
    variables, falling back to the local development certificates.
    """
    cert_file = cert_file or os.getenv("SSL_CERT_PATH", "localhost+1.pem")
    key_file = key_file or os.getenv("SSL_KEY_PATH", "localhost+1-key.pem")

    if not (Path(cert_file).exists() and Path(key_file).exists()):
        raise FileNotFoundError(
            f"SSL certificates not found: {cert_file}, {key_file}. "
            "Generate them using mkcert or update paths."
        )


def setup_schema(sql_path: str = "deployment/database_setup.sql") -> None:
    """Create database schema using the provided SQL file."""
    conn = create_database_connection()
    if not Path(sql_path).exists():
        raise FileNotFoundError(sql_path)
    with open(sql_path, "r", encoding="utf-8") as fh:
        sql = fh.read()
    for statement in sql.split(";"):
        stmt = statement.strip()
        if stmt:
            execute_command(conn, stmt + ";")


def create_performance_settings_table() -> None:
    """Create the performance_settings table if missing."""
    conn = create_database_connection()
    execute_command(
        conn,
        """
        CREATE TABLE IF NOT EXISTS performance_settings (
            setting_name VARCHAR(50) PRIMARY KEY,
            value VARCHAR(200) NOT NULL
        )
        """,
    )


def provision_admin_account(
    person_id: str = "admin", password_env: str = "ADMIN_PASSWORD"
) -> None:
    """Insert an initial admin account into the people table."""
    password = os.getenv(password_env)
    if not password:
        raise ValueError(f"{password_env} environment variable required")
    conn = create_database_connection()
    execute_command(
        conn,
        """
        INSERT INTO people (person_id, name, department, clearance_level, access_groups, is_visitor)
        VALUES (%s, 'Administrator', 'IT', 10, 'admin', false)
        ON CONFLICT (person_id) DO NOTHING
        """,
        (person_id,),
    )


__all__ = [
    "validate_environment",
    "ensure_ssl_certificates",
    "setup_schema",
    "create_performance_settings_table",
    "provision_admin_account",
]
