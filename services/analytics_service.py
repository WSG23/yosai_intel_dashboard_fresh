#!/usr/bin/env python3
"""
Analytics Service - Enhanced with Unique Patterns Analysis
"""
import pandas as pd
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from services.file_processing_service import FileProcessingService
from services.database_analytics_service import DatabaseAnalyticsService
from services.data_loader import DataLoader
from services.analytics_summary import (
    generate_basic_analytics,
    generate_sample_analytics,
    summarize_dataframe,
)

from utils.mapping_helpers import map_and_clean
from security.dataframe_validator import DataFrameSecurityValidator
from datetime import datetime, timedelta
import os


def ensure_analytics_config():
    """Emergency fix to ensure analytics configuration exists."""
    try:
        from config.dynamic_config import dynamic_config
        if not hasattr(dynamic_config, 'analytics'):
            from config.constants import AnalyticsConstants
            dynamic_config.analytics = AnalyticsConstants()
    except Exception:
        pass


ensure_analytics_config()

logger = logging.getLogger(__name__)


class AnalyticsDataAccessor:
    """Modular data accessor for analytics processing"""

    def __init__(self, base_data_path: str = "data"):
        self.base_path = Path(base_data_path)
        self.mappings_file = self.base_path / "learned_mappings.json"
        self.session_storage = self.base_path.parent / "session_storage"

    def get_processed_database(self) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Get the final processed database after column/device mapping"""
        mappings_data = self._load_consolidated_mappings()
        uploaded_data = self._get_uploaded_data()

        if not uploaded_data:
            return pd.DataFrame(), {}

        combined_df, metadata = self._apply_mappings_and_combine(uploaded_data, mappings_data)
        return combined_df, metadata

    def _load_consolidated_mappings(self) -> Dict[str, Any]:
        """Load consolidated mappings from learned_mappings.json"""
        try:
            if self.mappings_file.exists():
                with open(self.mappings_file, "r", encoding="utf-8", errors="replace") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading mappings: {e}")
            return {}

    def _get_uploaded_data(self) -> Dict[str, pd.DataFrame]:
        """Get uploaded data from file_upload module"""
        try:
            from pages.file_upload import get_uploaded_data
            uploaded_data = get_uploaded_data()

            if uploaded_data:
                logger.info(f"Found {len(uploaded_data):,} uploaded files")
                for filename, df in uploaded_data.items():
                    logger.info(f"{filename}: {len(df):,} rows")
                return uploaded_data
            else:
                logger.info("No uploaded data found")
                return {}

        except ImportError:
            logger.error("Could not import uploaded data from file_upload")
            return {}
        except Exception as e:
            logger.error(f"Error getting uploaded data: {e}")
            return {}

    def _apply_mappings_and_combine(self, uploaded_data: Dict[str, pd.DataFrame],
                                   mappings_data: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Apply learned mappings and combine all data"""
        combined_dfs = []
        metadata = {
            'total_files': len(uploaded_data),
            'processed_files': 0,
            'total_records': 0,
            'unique_users': set(),
            'unique_devices': set(),
            'date_range': {'start': None, 'end': None}
        }

        for filename, df in uploaded_data.items():
            try:
                mapped_df = self._apply_column_mappings(df, filename, mappings_data)
                enriched_df = self._apply_device_mappings(mapped_df, filename, mappings_data)

                enriched_df['source_file'] = filename
                enriched_df['processed_at'] = datetime.now()

                combined_dfs.append(enriched_df)
                metadata['processed_files'] += 1
                metadata['total_records'] += len(enriched_df)

                if 'person_id' in enriched_df.columns:
                    metadata['unique_users'].update(enriched_df['person_id'].dropna().unique())
                if 'door_id' in enriched_df.columns:
                    metadata['unique_devices'].update(enriched_df['door_id'].dropna().unique())

                if 'timestamp' in enriched_df.columns:
                    dates = pd.to_datetime(enriched_df['timestamp'], errors='coerce').dropna()
                    if len(dates) > 0:
                        if metadata['date_range']['start'] is None:
                            metadata['date_range']['start'] = dates.min()
                            metadata['date_range']['end'] = dates.max()
                        else:
                            metadata['date_range']['start'] = min(metadata['date_range']['start'], dates.min())
                            metadata['date_range']['end'] = max(metadata['date_range']['end'], dates.max())

            except Exception as e:
                logger.error(f"Error processing {filename}: {e}")
                continue

        if combined_dfs:
            final_df = pd.concat(combined_dfs, ignore_index=True)
            metadata['unique_users'] = len(metadata['unique_users'])
            metadata['unique_devices'] = len(metadata['unique_devices'])
            return final_df, metadata

        return pd.DataFrame(), metadata

    def _apply_column_mappings(self, df: pd.DataFrame, filename: str,
                              mappings_data: Dict[str, Any]) -> pd.DataFrame:
        """Apply learned column mappings and standard cleaning."""
        column_mappings = {}
        for mapping_info in mappings_data.values():
            if mapping_info.get('filename') == filename:
                column_mappings = mapping_info.get('column_mappings', {})
                break

        return map_and_clean(df, column_mappings)

    def _apply_device_mappings(self, df: pd.DataFrame, filename: str,
                              mappings_data: Dict[str, Any]) -> pd.DataFrame:
        """Apply learned device mappings"""
        if 'door_id' not in df.columns:
            return df

        device_mappings = {}
        for fingerprint, mapping_info in mappings_data.items():
            if mapping_info.get('filename') == filename:
                device_mappings = mapping_info.get('device_mappings', {})
                break

        if not device_mappings:
            return df

        device_attrs_df = pd.DataFrame.from_dict(device_mappings, orient='index')
        device_attrs_df.index.name = 'door_id'
        device_attrs_df.reset_index(inplace=True)

        enriched_df = df.merge(device_attrs_df, on='door_id', how='left')
        return enriched_df


class AnalyticsService:
    """Complete analytics service that integrates all data sources"""

    def __init__(self):
        self.database_manager: Optional[Any] = None
        self._initialize_database()
        self.file_processing_service = FileProcessingService()
        self.df_validator = DataFrameSecurityValidator()
        self.database_analytics_service = DatabaseAnalyticsService(
            self.database_manager
        )
        self.data_loader = DataLoader()

    def _initialize_database(self):
        """Initialize database connection"""
        try:
            from config.database_manager import DatabaseManager
            from config.config import get_database_config
            db_config = get_database_config()
            self.database_manager = DatabaseManager(db_config)
            logger.info("Database manager initialized")
            self.database_analytics_service = DatabaseAnalyticsService(
                self.database_manager
            )
        except Exception as e:
            logger.warning(f"Database initialization failed: {e}")
            self.database_manager = None

    def get_analytics_from_uploaded_data(self) -> Dict[str, Any]:
        """Get analytics from uploaded files using the FIXED file processor"""
        try:
            # Get uploaded file paths (not pre-processed data)
            from pages.file_upload import get_uploaded_filenames
            uploaded_files = get_uploaded_filenames()

            if not uploaded_files:
                return {'status': 'no_data', 'message': 'No uploaded files available'}

            combined_df, processing_info, processed_files, total_records = (
                self.file_processing_service.process_files(uploaded_files)
            )

            if combined_df.empty:
                return {
                    'status': 'error',
                    'message': 'No files could be processed successfully',
                    'processing_info': processing_info
                }

            # Generate analytics from the properly processed data
            analytics = generate_basic_analytics(combined_df)

            # Add processing information
            analytics.update({
                'data_source': 'uploaded_files_fixed',
                'total_files_processed': processed_files,
                'total_files_attempted': len(uploaded_files),
                'processing_info': processing_info,
                'total_events': total_records,
                'active_users': combined_df['person_id'].nunique() if 'person_id' in combined_df.columns else 0,
                'active_doors': combined_df['door_id'].nunique() if 'door_id' in combined_df.columns else 0,
                'timestamp': datetime.now().isoformat()
            })

            return analytics

        except Exception as e:
            logger.error(f"Error getting analytics from uploaded data: {e}")
            return {'status': 'error', 'message': str(e)}

    def get_analytics_by_source(self, source: str) -> Dict[str, Any]:
        """Get analytics from specified source with forced uploaded data check"""

        # FORCE CHECK: If uploaded data exists, use it regardless of source
        try:
            from pages.file_upload import get_uploaded_data
            uploaded_data = get_uploaded_data()

            if uploaded_data and source in ["uploaded", "sample"]:
                logger.info(f"Forcing uploaded data usage (source was: {source})")
                return self._process_uploaded_data_directly(uploaded_data)

        except Exception as e:
            logger.error(f"Uploaded data check failed: {e}")

        # Original logic for when no uploaded data
        if source == "sample":
            return generate_sample_analytics()
        elif source == "uploaded":
            return {'status': 'no_data', 'message': 'No uploaded files available'}
        elif source == "database":
            return self._get_database_analytics()
        else:
            return {'status': 'error', 'message': f'Unknown source: {source}'}

    def _process_uploaded_data_directly(self, uploaded_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process uploaded files without chunking and track per-file info."""
        try:
            from collections import Counter

            logger.info(f"Processing {len(uploaded_data)} uploaded files directly...")

            processing_info: Dict[str, Any] = {}
            total_events = 0
            user_counts: Counter[str] = Counter()
            door_counts: Counter[str] = Counter()
            min_ts: Optional[pd.Timestamp] = None
            max_ts: Optional[pd.Timestamp] = None

            for filename, source in uploaded_data.items():
                try:
                    if isinstance(source, (str, Path)):
                        df = pd.read_csv(source, encoding="utf-8")
                    else:
                        df = source

                    df = self.df_validator.validate(df)
                    df = map_and_clean(df)

                    processing_info[filename] = {"rows": len(df), "status": "ok"}
                except Exception as e:  # pragma: no cover - best effort
                    processing_info[filename] = {"rows": 0, "status": f"error: {e}"}
                    logger.error(f"Error processing {filename}: {e}")
                    continue

                total_events += len(df)

                if "person_id" in df.columns:
                    user_counts.update(df["person_id"].dropna().astype(str))
                if "door_id" in df.columns:
                    door_counts.update(df["door_id"].dropna().astype(str))
                if "timestamp" in df.columns:
                    ts = pd.to_datetime(df["timestamp"], errors="coerce").dropna()
                    if not ts.empty:
                        cur_min = ts.min()
                        cur_max = ts.max()
                        if min_ts is None or cur_min < min_ts:
                            min_ts = cur_min
                        if max_ts is None or cur_max > max_ts:
                            max_ts = cur_max

            if not processing_info:
                return {"status": "error", "message": "No uploaded files processed"}

            date_range = {"start": "Unknown", "end": "Unknown"}
            if min_ts is not None and max_ts is not None:
                date_range = {
                    "start": min_ts.strftime("%Y-%m-%d"),
                    "end": max_ts.strftime("%Y-%m-%d"),
                }

            active_users = len(user_counts)
            active_doors = len(door_counts)

            result = {
                "status": "success",
                "total_events": total_events,
                "active_users": active_users,
                "active_doors": active_doors,
                "unique_users": active_users,
                "unique_doors": active_doors,
                "data_source": "uploaded",
                "date_range": date_range,
                "top_users": [
                    {"user_id": u, "count": int(c)} for u, c in user_counts.most_common(10)
                ],
                "top_doors": [
                    {"door_id": d, "count": int(c)} for d, c in door_counts.most_common(10)
                ],
                "timestamp": datetime.now().isoformat(),
                "processing_info": processing_info,
            }

            return result

        except Exception as e:  # pragma: no cover - unexpected
            logger.error(f"Direct processing failed: {e}")
            return {"status": "error", "message": str(e)}

    # ------------------------------------------------------------------
    # Helper methods for processing uploaded data
    # ------------------------------------------------------------------
    def load_uploaded_data(self) -> Dict[str, pd.DataFrame]:
        """Load uploaded data from the file upload page."""
        try:
            from pages.file_upload import get_uploaded_data
            return get_uploaded_data() or {}
        except Exception as e:  # pragma: no cover - best effort
            logger.error(f"Error loading uploaded data: {e}")
            return {}

    def clean_uploaded_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply standard column mappings and basic cleaning."""
        return map_and_clean(df)

    def summarize_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Create a summary dictionary from a combined DataFrame."""
        return summarize_dataframe(df)

    def analyze_with_chunking(self, df: pd.DataFrame, analysis_types: List[str]) -> Dict[str, Any]:
        """FIXED: Analyze DataFrame using chunked processing - COMPLETE DATASET."""
        from security.dataframe_validator import DataFrameSecurityValidator
        from analytics.chunked_analytics_controller import ChunkedAnalyticsController

        original_rows = len(df)
        logger.info(f"🚀 Starting COMPLETE analysis for {original_rows:,} rows")

        validator = DataFrameSecurityValidator()
        df, needs_chunking = validator.validate_for_analysis(df)

        validated_rows = len(df)
        logger.info(f"📋 After validation: {validated_rows:,} rows, chunking needed: {needs_chunking}")

        # FIXED: Ensure we never lose data in validation
        if validated_rows != original_rows:
            logger.warning(f"⚠️  Row count changed during validation: {original_rows:,} → {validated_rows:,}")

        if not needs_chunking:
            logger.info("✅ Using regular analysis (no chunking needed)")
            return self._regular_analysis(df, analysis_types)

        # FIXED: Use proper chunk size calculation
        chunk_size = validator.get_optimal_chunk_size(df)
        chunked_controller = ChunkedAnalyticsController(chunk_size=chunk_size)

        logger.info(f"🔄 Using chunked analysis: {validated_rows:,} rows, {chunk_size:,} per chunk")

        # FIXED: Process with verification
        result = chunked_controller.process_large_dataframe(df, analysis_types)

        # FIXED: Add comprehensive processing summary
        result["processing_summary"] = {
            "original_input_rows": original_rows,
            "validated_rows": validated_rows,
            "rows_processed": result.get("rows_processed", validated_rows),
            "chunking_used": True,
            "chunk_size": chunk_size,
            "processing_complete": result.get("rows_processed", 0) == validated_rows,
            "data_integrity_check": "PASS" if result.get("rows_processed", 0) == validated_rows else "FAIL"
        }

        # FIXED: Verify complete processing
        rows_processed = result.get("rows_processed", 0)
        if rows_processed != validated_rows:
            logger.error(f"❌ PROCESSING ERROR: Expected {validated_rows:,} rows, got {rows_processed:,}")
        else:
            logger.info(f"✅ SUCCESS: Processed ALL {rows_processed:,} rows successfully")

        return result

    def diagnose_data_flow(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Diagnostic method to check data processing flow."""
        logger.info("=== Data Flow Diagnosis ===")
        logger.info(f"Input DataFrame: {len(df)} rows, {len(df.columns)} columns")
        logger.info(f"Memory usage: {df.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB")

        from security.dataframe_validator import DataFrameSecurityValidator
        validator = DataFrameSecurityValidator()

        logger.info(
            f"Validator config: upload_mb={validator.max_upload_mb}, analysis_mb={validator.max_analysis_mb}, chunk_size={validator.chunk_size}"
        )

        cleaned_df, needs_chunking = validator.validate_for_analysis(df.copy())
        logger.info(f"After validation: {len(cleaned_df)} rows, needs_chunking={needs_chunking}")

        if needs_chunking:
            chunk_size = validator.get_optimal_chunk_size(cleaned_df)
            logger.info(f"Optimal chunk size: {chunk_size}")

        return {
            "input_rows": len(df),
            "validated_rows": len(cleaned_df),
            "needs_chunking": needs_chunking,
            "validator_config": {
                "max_upload_mb": validator.max_upload_mb,
                "max_analysis_mb": validator.max_analysis_mb,
                "chunk_size": validator.chunk_size,
            },
        }

    def _regular_analysis(self, df: pd.DataFrame, analysis_types: List[str]) -> Dict[str, Any]:
        """Regular analysis for smaller DataFrames."""
        return summarize_dataframe(df)

    def _get_real_uploaded_data(self) -> Dict[str, Any]:
        """FIXED: Actually access your uploaded 395K records"""
        try:
            uploaded_data = self.load_uploaded_data()
            if not uploaded_data:
                return {'status': 'no_data', 'message': 'No uploaded files available'}

            logger.info(f"Processing {len(uploaded_data)} uploaded files...")

            all_dfs = []
            total_original_rows = 0

            for filename, df in uploaded_data.items():
                logger.info(f"Processing {filename}: {len(df):,} rows")
                cleaned = self.clean_uploaded_dataframe(df)
                all_dfs.append(cleaned)
                total_original_rows += len(df)

            combined_df = pd.concat(all_dfs, ignore_index=True)

            logger.info(f"Combined: {len(combined_df):,} total rows")

            summary = self.summarize_dataframe(combined_df)
            summary.update({
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'files_processed': len(uploaded_data),
                'original_total_rows': total_original_rows,
            })

            logger.info("Analytics result:")
            logger.info(f"Total Events: {summary['total_events']:,}")
            logger.info(f"Active Users: {summary['active_users']:,}")
            logger.info(f"Active Doors: {summary['active_doors']:,}")

            return summary

        except Exception as e:
            logger.error(f"Error processing uploaded data: {e}")
            return {
                'status': 'error',
                'message': f'Error processing uploaded data: {str(e)}',
                'total_events': 0
            }


    def _get_analytics_with_fixed_processor(self) -> Dict[str, Any]:
        """Get analytics using the FIXED file processor"""

        from config.config import get_sample_files_config

        sample_cfg = get_sample_files_config()
        csv_file = os.getenv("SAMPLE_CSV_PATH", sample_cfg.csv_path)
        json_file = os.getenv("SAMPLE_JSON_PATH", sample_cfg.json_path)

        try:
            from services import FileProcessor
            import pandas as pd
            import json

            processor = FileProcessor(upload_folder="temp", allowed_extensions={'csv', 'json', 'xlsx'})
            all_data = []

            # Process CSV with FIXED processor
            if os.path.exists(csv_file):
                df_csv = pd.read_csv(csv_file)
                result = processor._validate_data(df_csv)
                if result['valid']:
                    processed_df = result['data']
                    processed_df['source_file'] = 'csv'
                    all_data.append(processed_df)

            # Process JSON with FIXED processor
            if os.path.exists(json_file):
                with open(json_file, 'r', encoding='utf-8', errors='replace') as f:
                    json_data = json.load(f)
                df_json = pd.DataFrame(json_data)
                result = processor._validate_data(df_json)
                if result['valid']:
                    processed_df = result['data']
                    processed_df['source_file'] = 'json'
                    all_data.append(processed_df)

            if all_data:
                combined_df = pd.concat(all_data, ignore_index=True)

                return {
                    'status': 'success',
                    'total_events': len(combined_df),
                    'active_users': combined_df['person_id'].nunique(),
                    'active_doors': combined_df['door_id'].nunique(),
                    'data_source': 'fixed_processor',
                    'timestamp': datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"Error in fixed processor analytics: {e}")
            return {'status': 'error', 'message': str(e)}

        return {'status': 'no_data', 'message': 'Files not available'}

    def _get_database_analytics(self) -> Dict[str, Any]:
        """Get analytics from database"""
        if not self.database_analytics_service:
            return {'status': 'error', 'message': 'Database not available'}

        return self.database_analytics_service.get_analytics()

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get a basic dashboard summary"""
        try:
            summary = self.get_analytics_from_uploaded_data()
            return summary
        except Exception as e:
            logger.error(f"Dashboard summary failed: {e}")
            return {'status': 'error', 'message': str(e)}

    def get_unique_patterns_analysis(self, data_source: str | None = None):
        """Get unique patterns analysis for the requested source."""
        import logging
        logger = logging.getLogger(__name__)

        try:
            logger.info("🎯 Starting Unique Patterns Analysis")

            # STEP 1: Get uploaded data with verification
            if data_source == "database":
                df, _meta = self.data_loader.get_processed_database()
                uploaded_data = {"database": df} if not df.empty else {}
            else:
                from pages.file_upload import get_uploaded_data
                uploaded_data = get_uploaded_data()

            if not uploaded_data:
                logger.warning("❌ No uploaded data found for unique patterns analysis")
                return {
                    'status': 'no_data',
                    'message': 'No uploaded files available',
                    'data_summary': {'total_records': 0}
                }

            # STEP 2: Process the uploaded data
            logger.info(f"📁 Found {len(uploaded_data)} uploaded files")

            # Get the first file (or combine all files)
            all_dfs = []
            total_original_rows = 0

            for filename, df in uploaded_data.items():
                original_rows = len(df)
                total_original_rows += original_rows
                logger.info(f"   {filename}: {original_rows:,} rows")

                # Clean and map the dataframe
                cleaned_df = self.clean_uploaded_dataframe(df)
                all_dfs.append(cleaned_df)

                logger.info(f"   After cleaning: {len(cleaned_df):,} rows")

            # STEP 3: Combine all dataframes
            if len(all_dfs) == 1:
                combined_df = all_dfs[0]
            else:
                combined_df = pd.concat(all_dfs, ignore_index=True)

            final_rows = len(combined_df)
            logger.info(f"📊 COMBINED DATASET: {final_rows:,} total rows")

            # STEP 4: Check for data loss
            if final_rows != total_original_rows:
                logger.warning(f"⚠️  Data loss detected: {total_original_rows:,} → {final_rows:,}")

            # STEP 5: Verify we have the expected data
            if final_rows == 150 and total_original_rows > 150:
                logger.error("🚨 FOUND 150 ROW LIMIT in unique patterns analysis!")
                logger.error(f"   Original rows: {total_original_rows:,}")
                logger.error(f"   Final rows: {final_rows:,}")
                # Continue processing but log the issue
            elif final_rows > 1000:
                logger.info(f"✅ Processing large dataset: {final_rows:,} rows")

            # STEP 6: Calculate statistics
            total_records = len(combined_df)
            unique_users = combined_df['person_id'].nunique() if 'person_id' in combined_df.columns else 0
            unique_devices = combined_df['door_id'].nunique() if 'door_id' in combined_df.columns else 0

            logger.info("📈 STATISTICS:")
            logger.info(f"   Total records: {total_records:,}")
            logger.info(f"   Unique users: {unique_users:,}")
            logger.info(f"   Unique devices: {unique_devices:,}")

            # STEP 7: Calculate date range
            date_span = 0
            if 'timestamp' in combined_df.columns:
                combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'], errors='coerce')
                valid_dates = combined_df['timestamp'].dropna()
                if len(valid_dates) > 0:
                    date_span = (valid_dates.max() - valid_dates.min()).days
                    logger.info(f"   Date span: {date_span} days")

            # STEP 8: Analyze user patterns
            power_users = []
            regular_users = []
            occasional_users = []

            if 'person_id' in combined_df.columns and unique_users > 0:
                user_stats = combined_df.groupby('person_id').size()

                if len(user_stats) > 0:
                    # Calculate thresholds
                    q80 = user_stats.quantile(0.8)
                    q20 = user_stats.quantile(0.2)

                    power_users = user_stats[user_stats > q80].index.tolist()
                    regular_users = user_stats[user_stats.between(q20, q80)].index.tolist()
                    occasional_users = user_stats[user_stats < q20].index.tolist()

                    logger.info(f"   Power users: {len(power_users)}")
                    logger.info(f"   Regular users: {len(regular_users)}")
                    logger.info(f"   Occasional users: {len(occasional_users)}")

            # STEP 9: Analyze device patterns
            high_traffic_devices = []
            moderate_traffic_devices = []
            low_traffic_devices = []

            if 'door_id' in combined_df.columns and unique_devices > 0:
                device_stats = combined_df.groupby('door_id').size()

                if len(device_stats) > 0:
                    # Calculate thresholds
                    q80 = device_stats.quantile(0.8)
                    q20 = device_stats.quantile(0.2)

                    high_traffic_devices = device_stats[device_stats > q80].index.tolist()
                    moderate_traffic_devices = device_stats[device_stats.between(q20, q80)].index.tolist()
                    low_traffic_devices = device_stats[device_stats < q20].index.tolist()

                    logger.info(f"   High traffic devices: {len(high_traffic_devices)}")
                    logger.info(f"   Moderate traffic devices: {len(moderate_traffic_devices)}")
                    logger.info(f"   Low traffic devices: {len(low_traffic_devices)}")

            # STEP 10: Calculate interactions
            total_interactions = 0
            if 'person_id' in combined_df.columns and 'door_id' in combined_df.columns:
                interaction_pairs = combined_df.groupby(['person_id', 'door_id']).size()
                total_interactions = len(interaction_pairs)
                logger.info(f"   Total unique interactions: {total_interactions:,}")

            # STEP 11: Calculate success rate
            success_rate = 0.0
            if 'access_result' in combined_df.columns:
                success_mask = combined_df['access_result'].str.lower().str.contains(
                    'grant|allow|success|permit', case=False, na=False
                )
                success_rate = success_mask.mean()
                logger.info(f"   Success rate: {success_rate:.2%}")

            # STEP 12: Build the complete result
            result = {
                'status': 'success',
                'analysis_timestamp': datetime.now().isoformat(),

                # CRITICAL: This is what shows in the "Database Overview" card
                'data_summary': {
                    'total_records': total_records,  # This MUST be your actual row count
                    'unique_entities': {
                        'users': unique_users,
                        'devices': unique_devices,
                        'interactions': total_interactions
                    },
                    'date_range': {
                        'span_days': date_span
                    }
                },

                'user_patterns': {
                    'total_unique_users': unique_users,
                    'user_classifications': {
                        'power_users': power_users[:10],  # Limit for display
                        'regular_users': regular_users[:10],
                        'occasional_users': occasional_users[:10]
                    }
                },

                'device_patterns': {
                    'total_unique_devices': unique_devices,
                    'device_classifications': {
                        'high_traffic_devices': high_traffic_devices[:10],
                        'moderate_traffic_devices': moderate_traffic_devices[:10],
                        'low_traffic_devices': low_traffic_devices[:10],
                        'secure_devices': [],  # Placeholder
                        'popular_devices': high_traffic_devices[:5],
                        'problematic_devices': []  # Placeholder
                    }
                },

                'interaction_patterns': {
                    'total_unique_interactions': total_interactions,
                    'interaction_statistics': {
                        'unique_pairs': total_interactions
                    }
                },

                'temporal_patterns': {
                    'date_span_days': date_span
                },

                'access_patterns': {
                    'overall_success_rate': success_rate,
                    'success_percentage': success_rate * 100
                },

                'recommendations': []  # Placeholder
            }

            # STEP 13: Final verification log
            result_total = result['data_summary']['total_records']
            logger.info("🎉 UNIQUE PATTERNS ANALYSIS COMPLETE")
            logger.info(f"   Result total_records: {result_total:,}")

            if result_total == 150 and result_total != total_original_rows:
                logger.error("❌ STILL SHOWING 150 - CHECK DATA PROCESSING!")
            elif result_total == total_original_rows:
                logger.info(f"✅ SUCCESS: Correctly showing {result_total:,} rows")
            else:
                logger.warning(f"⚠️  Unexpected count: {result_total:,} (expected {total_original_rows:,})")

            return result

        except Exception as e:
            logger.error(f"❌ Unique patterns analysis failed: {e}")
            import traceback
            traceback.print_exc()

            return {
                'status': 'error',
                'message': f'Unique patterns analysis failed: {str(e)}',
                'data_summary': {'total_records': 0}
            }

    def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        health = {
            'service': 'healthy',
            'timestamp': datetime.now().isoformat()
        }

        # Check database
        if self.database_manager:
            try:
                health['database'] = 'healthy' if self.database_manager.health_check() else 'unhealthy'
            except:
                health['database'] = 'unhealthy'
        else:
            health['database'] = 'not_configured'

        # Check file upload
        try:
            from pages.file_upload import get_uploaded_filenames
            health['uploaded_files'] = len(get_uploaded_filenames())
        except ImportError:
            health['uploaded_files'] = 'not_available'

        return health

    def get_data_source_options(self) -> List[Dict[str, str]]:
        """Get available data source options"""
        options = [
            {"label": "Sample Data", "value": "sample"}
        ]

        # Check for uploaded data
        try:
            from pages.file_upload import get_uploaded_filenames
            uploaded_files = get_uploaded_filenames()
            if uploaded_files:
                options.append({"label": f"Uploaded Files ({len(uploaded_files)})", "value": "uploaded"})
        except ImportError:
            pass

        # Check for database
        if self.database_manager and self.database_manager.health_check():
            options.append({"label": "Database", "value": "database"})

        return options

    def get_date_range_options(self) -> Dict[str, str]:
        """Get default date range options"""
        from datetime import datetime, timedelta
        return {
            'start': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
            'end': datetime.now().strftime('%Y-%m-%d')
        }

    def get_analytics_status(self) -> Dict[str, Any]:
        """Get current analytics status"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'data_sources_available': len(self.get_data_source_options()),
            'service_health': self.health_check()
        }

        try:
            from pages.file_upload import get_uploaded_filenames
            status['uploaded_files'] = len(get_uploaded_filenames())
        except ImportError:
            status['uploaded_files'] = 0

        return status

# Global service instance
_analytics_service: Optional[AnalyticsService] = None

def get_analytics_service(service: Optional[AnalyticsService] = None) -> AnalyticsService:
    """Return a global analytics service instance.

    If ``service`` is provided, it becomes the global instance.  Otherwise an
    instance is created on first access.
    """
    global _analytics_service
    if service is not None:
        _analytics_service = service
    if _analytics_service is None:
        _analytics_service = AnalyticsService()
    return _analytics_service

def create_analytics_service() -> AnalyticsService:
    """Create new analytics service instance"""
    return AnalyticsService()

__all__ = ['AnalyticsService', 'get_analytics_service', 'create_analytics_service']
