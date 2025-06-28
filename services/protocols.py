"""
Service protocols for type safety and dependency injection
"""
from typing import Protocol, Any, Dict, List, Optional
import pandas as pd

class DatabaseProtocol(Protocol):
    """Protocol for database services"""
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> pd.DataFrame:
        """Execute a query and return results as DataFrame"""
        ...
    
    def execute_command(self, command: str, params: Optional[tuple] = None) -> bool:
        """Execute a command (INSERT, UPDATE, DELETE)"""
        ...
    
    def health_check(self) -> Dict[str, Any]:
        """Check database health"""
        ...

class AnalyticsProtocol(Protocol):
    """Protocol for analytics services"""
    
    def get_summary_stats(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Get summary statistics"""
        ...
    
    def detect_anomalies(self, data: pd.DataFrame) -> pd.DataFrame:
        """Detect anomalies in data"""
        ...
    
    def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        ...

class FileProcessorProtocol(Protocol):
    """Protocol for file processing services"""
    
    def process_file(self, file_content: bytes, filename: str) -> pd.DataFrame:
        """Process uploaded file"""
        ...
    
    def validate_file(self, filename: str, content: bytes) -> Dict[str, Any]:
        """Validate file before processing"""
        ...
    
    def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        ...
