# services/file_processor.py
import pandas as pd
import json
import os
import uuid
from typing import Dict, Any, Optional, Tuple, Sequence
import logging
from datetime import datetime

class FileProcessor:
    """Service for processing uploaded files"""
    
    def __init__(self, upload_folder: str, allowed_extensions: set):
        self.upload_folder = upload_folder
        self.allowed_extensions = allowed_extensions
        
        # Ensure upload folder exists
        os.makedirs(upload_folder, exist_ok=True)
    
    def process_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Process uploaded file and return parsed data"""
        
        if not self._is_allowed_file(filename):
            return {
                'success': False,
                'error': f'File type not allowed. Allowed: {self.allowed_extensions}'
            }
        
        try:
            # Save file temporarily
            file_id = str(uuid.uuid4())
            file_path = os.path.join(self.upload_folder, f"{file_id}_{filename}")
            
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Parse based on file type
            file_ext = filename.rsplit('.', 1)[1].lower()
            
            if file_ext == 'csv':
                df = self._parse_csv(file_path)
            elif file_ext == 'json':
                df = self._parse_json(file_path)
            elif file_ext in ['xlsx', 'xls']:
                df = self._parse_excel(file_path)
            else:
                return {'success': False, 'error': 'Unsupported file type'}
            
            # Validate and clean data
            validation_result = self._validate_data(df)
            
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': validation_result['error'],
                    'suggestions': validation_result.get('suggestions', [])
                }
            
            # Clean up temporary file
            os.remove(file_path)
            
            return {
                'success': True,
                'data': df,
                'filename': filename,
                'rows': len(df),
                'columns': list(df.columns),
                'file_id': file_id,
                'processed_at': datetime.now()
            }
            
        except Exception as e:
            logging.error(f"Error processing file {filename}: {e}")
            return {
                'success': False,
                'error': f'Error processing file: {str(e)}'
            }
    
    def _parse_csv(self, file_path: str) -> pd.DataFrame:
        """Parse CSV file using pandas automatic delimiter detection"""

        # Detect header with automatic delimiter detection
        header = pd.read_csv(file_path, nrows=0, sep=None, engine="python").columns
        parse_dates = ["timestamp"] if "timestamp" in header else False

        # Read the entire file once using the detected delimiter
        return pd.read_csv(
            file_path,
            sep=None,
            engine="python",
            encoding="utf-8",
            parse_dates=parse_dates,
        )
    
    def _parse_json(self, file_path: str) -> pd.DataFrame:
        """Parse JSON file"""
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different JSON structures
        if isinstance(data, list):
            return pd.DataFrame(data)
        elif isinstance(data, dict):
            if 'data' in data:
                return pd.DataFrame(data['data'])
            else:
                return pd.DataFrame([data])
        else:
            raise ValueError("Unsupported JSON structure")
    
    def _parse_excel(self, file_path: str) -> pd.DataFrame:
        """Parse Excel file"""
        
        # Try to read the first sheet
        excel_file = pd.ExcelFile(file_path)
        
        # Get the first sheet name
        sheet_name = excel_file.sheet_names[0]
        
        df = pd.read_excel(
            file_path, 
            sheet_name=sheet_name,
            parse_dates=['timestamp'] if 'timestamp' in pd.read_excel(file_path, nrows=0).columns else False
        )
        
        return df
    
    def _validate_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Enhanced validation with automatic column mapping - NO EMOJIS"""

        if df.empty:
            return {'valid': False, 'error': 'File is empty'}

        # Required columns for access control data
        required_columns = ['person_id', 'door_id', 'access_result', 'timestamp']

        logger.info(f"[INFO] Validating data: {len(df)} rows, columns: {list(df.columns)}")

        # Check for exact matches first
        exact_matches = [col for col in required_columns if col in df.columns]
        missing_columns = [col for col in required_columns if col not in df.columns]

        logger.info(f"[INFO] Exact matches: {exact_matches}, Missing: {missing_columns}")

        # If we have all exact matches, proceed with validation
        if len(exact_matches) == len(required_columns):
            logger.info("[SUCCESS] All columns found exactly, proceeding with validation")
            return self._validate_data_content(df)

        # Try fuzzy matching for missing columns
        if missing_columns:
            logger.info("[INFO] Attempting fuzzy matching...")
            fuzzy_matches = self._fuzzy_match_columns(list(df.columns), required_columns)

            logger.info(f"[INFO] Fuzzy matches found: {fuzzy_matches}")

            # Check if we found matches for all required columns
            if len(fuzzy_matches) >= len(missing_columns):
                # Apply column mappings
                logger.info("[SUCCESS] Applying column mappings...")
                try:
                    df_mapped = df.copy()
                    # FIX: Invert the dictionary - fuzzy_matches is target->source, but rename needs source->target
                    rename_dict = {source_col: target_col for target_col, source_col in fuzzy_matches.items()}
                    df_mapped = df_mapped.rename(columns=rename_dict)
                    
                    logger.info(f"[SUCCESS] Applied rename dict: {rename_dict}")
                    logger.info(f"[INFO] New columns: {list(df_mapped.columns)}")
                    
                    # Validate the mapped dataframe and ensure column names are preserved
                    validation_result = self._validate_data_content(df_mapped)
                    
                    # Force the renamed dataframe to be returned
                    if validation_result['valid']:
                        validation_result['data'] = df_mapped  # Ensure the renamed df is returned
                        logger.info(f"[DEBUG] Returning dataframe with columns: {list(df_mapped.columns)}")
                    
                    return validation_result

                except Exception as e:
                    logger.info(f"[ERROR] Error applying column mappings: {e}")
                    return {
                        'valid': False,
                        'error': f'Error applying column mappings: {str(e)}',
                        'suggestions': fuzzy_matches
                    }
            else:
                missing_after_fuzzy = [col for col in required_columns if col not in fuzzy_matches]
                logger.info(f"[WARNING] Could not map all columns. Still missing: {missing_after_fuzzy}")
                return {
                    'valid': False,
                    'error': f'Could not map required columns. Missing: {missing_after_fuzzy}',
                    'suggestions': fuzzy_matches,
                    'available_columns': list(df.columns),
                    'required_columns': required_columns
                }

        # If we reach here, all exact matches were found
        validation_result = self._validate_data_content(df)
        return validation_result

    def _validate_data_content(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate the actual data content after column mapping - NO EMOJIS"""

        logger.info("[INFO] Validating data content...")
        validation_errors = []

        # Standardize access_result values if present
        if 'access_result' in df.columns:
            logger.info("[INFO] Standardizing access_result values...")
            original_values = df['access_result'].unique()
            logger.info(f"[INFO] Original access results: {original_values}")

            # Handle your specific format: "Access Granted" -> "Granted"
            df['access_result'] = df['access_result'].astype(str).str.replace('Access ', '', regex=False)
            standardized_values = df['access_result'].unique()
            logger.info(f"[INFO] Standardized access results: {standardized_values}")

            # Check for valid results (be more permissive)
            valid_results = ['granted', 'denied', 'timeout', 'error', 'failed']
            invalid_results = [r for r in df['access_result'].str.lower().unique() \
                             if r not in valid_results and r != 'nan']

            if invalid_results:
                logger.info(f"[WARNING] Non-standard access results found: {invalid_results} (will be processed anyway)")

        # Validate timestamp if present
        if 'timestamp' in df.columns:
            logger.info("[INFO] Validating timestamp column...")
            try:
                # Try to convert to datetime if not already
                if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

                # Check for invalid timestamps
                null_timestamps = df['timestamp'].isnull().sum()
                if null_timestamps > 0:
                    logger.info(f"[WARNING] Found {null_timestamps} invalid timestamps (will be processed anyway)")
            except Exception as e:
                logger.info(f"[WARNING] Timestamp validation error: {e} (will be processed anyway)")

        # Return validation result with the processed DataFrame
        if validation_errors:
            return {
                'valid': False,
                'error': '; '.join(validation_errors),
                'data': df  # Still return the DataFrame even if there are errors
            }
        else:
            return {
                'valid': True,
                'data': df,  # CRITICAL: Return the processed DataFrame
                'message': 'Data validation successful'
            }
    
    def _fuzzy_match_columns(self, available_columns: Sequence[str], required_columns: Sequence[str]) -> Dict[str, str]:
        """Enhanced fuzzy matching that handles your actual column names - NO EMOJIS"""

        suggestions = {}

        # Enhanced mapping patterns that match your actual data
        mapping_patterns = {
            'person_id': [
                # Exact matches for your data
                'person id', 'userid', 'user id',
                # General patterns  
                'user', 'employee', 'badge', 'card', 'person', 'emp',
                'employee_id', 'badge_id', 'card_id'
            ],
            'door_id': [
                # Exact matches for your data
                'device name', 'devicename', 'device_name',
                # General patterns
                'door', 'reader', 'device', 'access_point', 'gate', 'entry',
                'door_name', 'reader_id', 'access_device'
            ],
            'access_result': [
                # Exact matches for your data  
                'access result', 'accessresult', 'access_result',
                # General patterns
                'result', 'status', 'outcome', 'decision', 'success',
                'granted', 'denied', 'access_status'
            ],
            'timestamp': [
                # Exact matches for your data
                'timestamp', 'time', 'datetime', 'date',
                # General patterns  
                'when', 'occurred', 'event_time', 'access_time',
                'date_time', 'event_date'
            ]
        }

        # Convert available columns to lowercase for matching
        available_lower = {col.lower(): col for col in available_columns}

        # Find best matches
        for required_col, patterns in mapping_patterns.items():
            best_match = None

            # Try exact pattern matches first
            for pattern in patterns:
                if pattern.lower() in available_lower:
                    best_match = available_lower[pattern.lower()]
                    break

            # If no exact match, try substring matching
            if not best_match:
                for pattern in patterns:
                    for available_col_lower, original_col in available_lower.items():
                        if pattern in available_col_lower or available_col_lower in pattern:
                            best_match = original_col
                            break
                    if best_match:
                        break

            if best_match:
                suggestions[required_col] = best_match

        logger.info(f"[INFO] Fuzzy matching suggestions: {suggestions}")
        return suggestions

    def apply_manual_mapping(self, df: pd.DataFrame, column_mapping: Dict[str, str]) -> pd.DataFrame:
        """Apply manual column mapping provided by user"""

        logger.info(f"🔧 Applying manual mapping: {column_mapping}")

        missing_source_cols = [source for source in column_mapping.values() if source not in df.columns]
        if missing_source_cols:
            raise ValueError(f"Source columns not found: {missing_source_cols}")

        df_mapped = df.rename(columns={v: k for k, v in column_mapping.items()})

        return df_mapped

    def get_mapping_suggestions(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get mapping suggestions for user interface"""

        required_columns = ['person_id', 'door_id', 'access_result', 'timestamp']
        fuzzy_matches = self._fuzzy_match_columns(list(df.columns), required_columns)

        return {
            'available_columns': list(df.columns),
            'required_columns': required_columns,
            'suggested_mappings': fuzzy_matches,
            'missing_mappings': [col for col in required_columns if col not in fuzzy_matches]
        }
    
    def _is_allowed_file(self, filename: str) -> bool:
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
