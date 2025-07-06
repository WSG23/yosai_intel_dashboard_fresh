# core/protocols.py
"""
Protocol-oriented architecture inspired by Swift's approach
Defines clear contracts for all major system components
"""
from typing import Protocol, Dict, Any, Optional, List, Callable
from abc import abstractmethod
import pandas as pd
from datetime import datetime


class DatabaseProtocol(Protocol):
    """Protocol defining database operations contract"""

    @abstractmethod
    def execute_query(self, query: str, params: Optional[tuple] = None) -> pd.DataFrame:
        """Execute a query and return results as DataFrame"""
        ...

    @abstractmethod
    def execute_command(self, command: str, params: Optional[tuple] = None) -> None:
        """Execute a command (INSERT, UPDATE, DELETE)"""
        ...

    @abstractmethod
    def health_check(self) -> bool:
        """Verify database connectivity"""
        ...


class AnalyticsServiceProtocol(Protocol):
    """Protocol for analytics service operations"""

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


class FileProcessorProtocol(Protocol):
    """Protocol for file processing operations"""

    @abstractmethod
    def validate_file(self, filename: str, file_size: int) -> Dict[str, Any]:
        """Validate uploaded file"""
        ...

    @abstractmethod
    def process_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Process uploaded file and return structured data"""
        ...


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
    def reload_configuration(self) -> None:
        """Reload configuration from source"""
        ...


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


class CallbackProtocol(Protocol):
    """Protocol for services that wrap and validate callbacks"""

    @abstractmethod
    def wrap_callback(self, callback_func: Callable) -> Callable:
        """Return a wrapped, safe callback function"""
        ...

    @abstractmethod
    def validate_callback_output(self, output: Any) -> Any:
        """Validate and sanitize callback output"""
        ...


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
