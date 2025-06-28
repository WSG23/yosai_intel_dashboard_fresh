"""
File Processing Service for Yōsai Intel Dashboard
"""
import pandas as pd
import io
import logging
from typing import Dict, Any, List
from pathlib import Path

from .base import BaseService
from .protocols import FileProcessorProtocol

logger = logging.getLogger(__name__)

class FileProcessorService(BaseService):
    """File processing service implementation"""
    
    ALLOWED_EXTENSIONS = {'.csv', '.json', '.xlsx', '.xls'}
    MAX_FILE_SIZE_MB = 100
    
    def __init__(self):
        super().__init__("file_processor")
    
    def _do_initialize(self) -> None:
        """Initialize file processor"""
        pass  # No special initialization needed
    
    def validate_file(self, filename: str, content: bytes) -> Dict[str, Any]:
        """Validate uploaded file"""
        issues = []
        
        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in self.ALLOWED_EXTENSIONS:
            issues.append(f"File type {file_ext} not allowed. Allowed: {self.ALLOWED_EXTENSIONS}")
        
        # Check file size
        size_mb = len(content) / (1024 * 1024)
        if size_mb > self.MAX_FILE_SIZE_MB:
            issues.append(f"File too large: {size_mb:.1f}MB > {self.MAX_FILE_SIZE_MB}MB")
        
        # Check for empty file
        if len(content) == 0:
            issues.append("File is empty")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'size_mb': size_mb,
            'extension': file_ext
        }
    
    def process_file(self, file_content: bytes, filename: str) -> pd.DataFrame:
        """Process uploaded file and return DataFrame"""
        try:
            file_ext = Path(filename).suffix.lower()
            
            if file_ext == '.csv':
                return self._process_csv(file_content)
            elif file_ext == '.json':
                return self._process_json(file_content)
            elif file_ext in ['.xlsx', '.xls']:
                return self._process_excel(file_content)
            else:
                raise ValueError(f"Unsupported file type: {file_ext}")
                
        except Exception as e:
            logger.error(f"Error processing file {filename}: {e}")
            raise
    
    def _process_csv(self, content: bytes) -> pd.DataFrame:
        """Process CSV file"""
        try:
            # Try different encodings
            for encoding in ['utf-8', 'latin1', 'cp1252']:
                try:
                    text = content.decode(encoding)
                    return pd.read_csv(io.StringIO(text))
                except UnicodeDecodeError:
                    continue
            raise ValueError("Could not decode CSV file with any standard encoding")
        except Exception as e:
            raise ValueError(f"Error reading CSV: {e}")
    
    def _process_json(self, content: bytes) -> pd.DataFrame:
        """Process JSON file"""
        try:
            text = content.decode('utf-8')
            return pd.read_json(io.StringIO(text))
        except Exception as e:
            raise ValueError(f"Error reading JSON: {e}")
    
    def _process_excel(self, content: bytes) -> pd.DataFrame:
        """Process Excel file"""
        try:
            return pd.read_excel(io.BytesIO(content))
        except Exception as e:
            raise ValueError(f"Error reading Excel file: {e}")
