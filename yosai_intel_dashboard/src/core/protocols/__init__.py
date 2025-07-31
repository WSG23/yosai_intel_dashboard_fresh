# core/protocols.py
"""
Protocol-oriented architecture inspired by Swift's approach
Defines clear contracts for all major system components
"""
"""Protocol interfaces for core services used across the project."""

from abc import abstractmethod
from datetime import datetime
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Protocol,
    Tuple,
    runtime_checkable,
)

import pandas as pd

from yosai_intel_dashboard.src.infrastructure.callbacks.events import CallbackEvent


@runtime_checkable
class DatabaseProtocol(Protocol):
    """Protocol defining database operations contract."""

    @abstractmethod
    def execute_query(self, query: str, params: Optional[tuple] = None) -> pd.DataFrame:
        """Execute a query and return results as DataFrame"""
        ...

    @abstractmethod
    def execute_command(self, command: str, params: Optional[tuple] = None) -> None:
        """Execute a command (INSERT, UPDATE, DELETE)"""
        ...

    @abstractmethod
    def begin_transaction(self) -> Any:
        """Begin database transaction."""
        ...

    @abstractmethod
    def commit_transaction(self, transaction: Any) -> None:
        """Commit database transaction."""
        ...

    @abstractmethod
    def rollback_transaction(self, transaction: Any) -> None:
        """Rollback database transaction."""
        ...

    @abstractmethod
    def health_check(self) -> bool:
        """Verify database connectivity and health."""
        ...

    @abstractmethod
    def get_connection_info(self) -> Dict[str, Any]:
        """Get database connection information."""
        ...


@runtime_checkable
class AnalyticsServiceProtocol(Protocol):
    """Protocol for analytics service operations."""

    data_loader: Any
    analytics_processor: Any
    summary_reporter: Any

    @abstractmethod
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get main dashboard summary statistics"""
        ...

    @abstractmethod
    def analyze_access_patterns(self, days: int) -> Dict[str, Any]:
        """Analyze access patterns over specified days"""
        ...

    @abstractmethod
    def detect_anomalies(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect anomalies in access data"""
        ...

    @abstractmethod
    def generate_report(
        self, report_type: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate analytics report of specified type."""
        ...


@runtime_checkable
class FileProcessorProtocol(Protocol):
    """Protocol for processing uploaded file contents."""

    @abstractmethod
    async def process_file(
        self,
        content: str,
        filename: str,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> pd.DataFrame:
        """Process uploaded file content into a DataFrame."""
        ...

    @abstractmethod
    def read_uploaded_file(
        self, contents: str, filename: str
    ) -> Tuple[pd.DataFrame, str]:
        """Read an uploaded file and return a DataFrame and error."""
        ...


@runtime_checkable
class ConfigurationProtocol(Protocol):
    """Protocol for configuration management"""

    @abstractmethod
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        ...

    @abstractmethod
    def get_app_config(self) -> Dict[str, Any]:
        """Get application configuration"""
        ...

    @abstractmethod
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration settings."""
        ...

    @abstractmethod
    def get_upload_config(self) -> Dict[str, Any]:
        """Get upload configuration settings."""
        ...

    @abstractmethod
    def reload_config(self) -> None:
        """Reload configuration from source."""
        ...

    @abstractmethod
    def validate_config(self) -> Dict[str, Any]:
        """Validate current configuration."""
        ...


@runtime_checkable
class SerializationProtocol(Protocol):
    """Protocol for JSON serialization services"""

    @abstractmethod
    def serialize(self, data: Any) -> str:
        """Serialize data to a JSON string"""
        ...

    @abstractmethod
    def sanitize_for_transport(self, data: Any) -> Any:
        """Prepare data for network transport"""
        ...

    @abstractmethod
    def is_serializable(self, data: Any) -> bool:
        """Check if the given data can be serialized"""
        ...


@runtime_checkable
class CallbackProtocol(Protocol):
    """Protocol for services that wrap and validate callbacks"""

    @abstractmethod
    def handle_wrap(self, callback_func: Callable) -> Callable:
        """Return a wrapped, safe callback function"""
        ...

    @abstractmethod
    def validate_callback_output(self, output: Any) -> Any:
        """Validate and sanitize callback output"""
        ...


@runtime_checkable
class ConfigProviderProtocol(Protocol):
    """Protocol for objects that supply configuration sections."""

    @abstractmethod
    def get_analytics_config(self) -> Dict[str, Any]:
        """Return analytics configuration."""
        ...

    @abstractmethod
    def get_database_config(self) -> Dict[str, Any]:
        """Return database configuration."""
        ...

    @abstractmethod
    def get_security_config(self) -> Dict[str, Any]:
        """Return security configuration."""
        ...


@runtime_checkable
class ConfigurationServiceProtocol(Protocol):
    """Interface for accessing runtime configuration values."""

    def get_max_upload_size_mb(self) -> int: ...

    def get_max_upload_size_bytes(self) -> int: ...

    def validate_large_file_support(self) -> bool: ...

    def get_upload_chunk_size(self) -> int: ...

    def get_max_parallel_uploads(self) -> int: ...

    def get_validator_rules(self) -> Dict[str, Any]: ...

    def get_ai_confidence_threshold(self) -> int: ...

    def get_db_pool_size(self) -> int: ...


@runtime_checkable
class SecurityServiceProtocol(Protocol):
    """Protocol for security validation operations."""

    @abstractmethod
    def validate_input(self, value: str, field_name: str = "input") -> Dict[str, Any]:
        """Validate user input for security threats."""
        ...

    @abstractmethod
    def validate_file_upload(self, filename: str, content: bytes) -> Dict[str, Any]:
        """Validate uploaded file for security compliance."""
        ...

    @abstractmethod
    def sanitize_output(self, content: str) -> str:
        """Sanitize content for safe output."""
        ...

    @abstractmethod
    def check_permissions(self, user_id: str, resource: str, action: str) -> bool:
        """Check user permissions for resource action."""
        ...


@runtime_checkable
class StorageProtocol(Protocol):
    """Protocol for generic data storage operations."""

    @abstractmethod
    def store_data(self, key: str, data: Any) -> str:
        """Store data and return storage identifier."""
        ...

    @abstractmethod
    def retrieve_data(self, key: str) -> Any:
        """Retrieve data by key."""
        ...

    @abstractmethod
    def delete_data(self, key: str) -> bool:
        """Delete data by key."""
        ...

    @abstractmethod
    def list_keys(self, prefix: str = "") -> List[str]:
        """List storage keys with optional prefix filter."""
        ...

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists in storage."""
        ...

    @abstractmethod
    def get_storage_info(self) -> Dict[str, Any]:
        """Get storage system information."""
        ...


@runtime_checkable
class LoggingProtocol(Protocol):
    """Protocol for logging operations."""

    @abstractmethod
    def log_info(self, message: str, **kwargs) -> None:
        """Log informational message."""
        ...

    @abstractmethod
    def log_warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        ...

    @abstractmethod
    def log_error(self, message: str, error: Exception | None = None, **kwargs) -> None:
        """Log error message."""
        ...

    @abstractmethod
    def log_debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        ...

    @abstractmethod
    def set_log_level(self, level: str) -> None:
        """Set logging level."""
        ...

    @abstractmethod
    def get_log_level(self) -> str:
        """Get current log level."""
        ...


@runtime_checkable
class EventBusProtocol(Protocol):
    """Protocol for simple event bus operations."""

    @abstractmethod
    def publish(
        self, event_type: str, data: Dict[str, Any], source: str | None = None
    ) -> None:
        """Publish event to bus."""
        ...

    @abstractmethod
    def subscribe(self, event_type: str, handler: Callable, priority: int = 0) -> str:
        """Subscribe to event type, return subscription ID."""
        ...

    @abstractmethod
    def unsubscribe(self, subscription_id: str) -> None:
        """Unsubscribe from event."""
        ...

    @abstractmethod
    def get_subscribers(self, event_type: str | None = None) -> List[Dict[str, Any]]:
        """Get current subscribers for event type."""
        ...

    @abstractmethod
    def get_event_history(
        self, event_type: str | None = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get event history, optionally filtered by type."""
        ...


@runtime_checkable
class ExportServiceProtocol(Protocol):
    """Protocol for data export operations."""

    @abstractmethod
    def export_to_csv(self, data: pd.DataFrame, filename: str) -> str:
        """Export data to CSV format."""
        ...

    @abstractmethod
    def export_to_excel(self, data: pd.DataFrame, filename: str) -> str:
        """Export data to Excel format."""
        ...

    @abstractmethod
    def export_to_pdf(self, data: Dict[str, Any], template: str) -> str:
        """Export data to PDF using template."""
        ...

    @abstractmethod
    def get_export_status(self, export_id: str) -> Dict[str, Any]:
        """Get status of export operation."""
        ...


@runtime_checkable
class CacheProtocol(Protocol):
    """Protocol for caching operations."""

    @abstractmethod
    def get(self, key: str) -> Any:
        """Get value from cache."""
        ...

    @abstractmethod
    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache with optional TTL."""
        ...

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        ...

    @abstractmethod
    def clear(self) -> None:
        """Clear all cache entries."""
        ...

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        ...


@runtime_checkable
class CallbackSystemProtocol(Protocol):
    """Protocol for the unified callback system."""

    @abstractmethod
    def handle_register_event(
        self,
        event: CallbackEvent,
        func: Callable[..., Any],
        *,
        priority: int = 50,
        secure: bool = False,
        timeout: Optional[float] = None,
        retries: int = 0,
    ) -> None:
        """Register a callback for an event."""
        ...

    @abstractmethod
    def trigger_event(
        self, event: CallbackEvent, *args: Any, **kwargs: Any
    ) -> List[Any]:
        """Synchronously trigger callbacks for an event."""
        ...

    @abstractmethod
    async def trigger_event_async(
        self, event: CallbackEvent, *args: Any, **kwargs: Any
    ) -> List[Any]:
        """Asynchronously trigger callbacks for an event."""
        ...


@runtime_checkable
class UnicodeProcessorProtocol(Protocol):
    """Protocol for Unicode text processing utilities."""

    @abstractmethod
    def clean_text(self, text: str, replacement: str = "") -> str:
        """Clean surrogate characters and unsafe control codes from text."""
        ...

    @abstractmethod
    def safe_encode_text(self, value: Any) -> str:
        """Safely encode any value to Unicode text."""
        ...

    @abstractmethod
    def safe_decode_text(self, data: bytes, encoding: str = "utf-8") -> str:
        """Safely decode byte data to text."""
        ...


from yosai_intel_dashboard.src.infrastructure.di.service_container import ServiceContainer


def _get_container(
    container: ServiceContainer | None = None,
) -> ServiceContainer | None:
    if container is not None:
        return container
    try:  # pragma: no cover - dash may be missing in tests
        from dash import get_app

        app = get_app()
        return getattr(app, "_service_container", None)
    except Exception:
        return None


def get_unicode_processor(
    container: ServiceContainer | None = None,
) -> UnicodeProcessorProtocol:
    c = _get_container(container)
    if c and c.has("unicode_processor"):
        return c.get("unicode_processor")
    from core.unicode import UnicodeProcessor

    return UnicodeProcessor()
