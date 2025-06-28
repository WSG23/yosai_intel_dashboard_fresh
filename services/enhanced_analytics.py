# services/enhanced_analytics.py
"""
Enhanced analytics service with Apple-quality data processing
Implements advanced analytics patterns and optimizations
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
import warnings

from core.protocols import AnalyticsServiceProtocol
from core.performance import measure_performance, MetricType, PerformanceContext
from core.error_handling import with_error_handling, ErrorCategory, ErrorSeverity

class AnalysisType(Enum):
    """Types of analytics analyses"""
    DESCRIPTIVE = "descriptive"
    DIAGNOSTIC = "diagnostic"
    PREDICTIVE = "predictive"
    PRESCRIPTIVE = "prescriptive"

class AnomalyType(Enum):
    """Types of anomalies detected"""
    STATISTICAL = "statistical"
    PATTERN = "pattern"
    BEHAVIORAL = "behavioral"
    TEMPORAL = "temporal"
    VOLUME = "volume"

@dataclass
class AnalysisResult:
    """Result of an analytics operation"""
    analysis_type: AnalysisType
    timestamp: datetime
    data_points: int
    processing_time: float
    confidence: float
    results: Dict[str, Any]
    metadata: Dict[str, Any]

@dataclass
class AnomalyDetection:
    """Anomaly detection result"""
    anomaly_id: str
    anomaly_type: AnomalyType
    timestamp: datetime
    confidence: float
    severity: str
    description: str
    affected_records: List[str]
    suggested_actions: List[str]
    metadata: Dict[str, Any]

class EnhancedAnalyticsService:
    """
    Production-grade analytics service with comprehensive data processing
    """
    
    def __init__(self, database_connection, cache_manager=None):
        self.db = database_connection
        self.cache = cache_manager
        self.logger = logging.getLogger(__name__)
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        
        # Suppress pandas warnings for cleaner output
        warnings.filterwarnings('ignore', category=pd.errors.PerformanceWarning)

    def get_enhanced_dashboard_summary(self, time_range_hours: int = 24) -> Dict[str, Any]:
        """Get comprehensive dashboard summary with AI column mapping"""

        def apply_ai_column_mapping(df, session_id="analytics_session"):
            """Use AI mapping service instead of manual mapping"""
            try:
                # Try to get AI classification plugin
                from plugins.ai_classification.plugin import AIClassificationPlugin
                from plugins.ai_classification.config import get_ai_config

                # Initialize AI plugin if available
                ai_plugin = AIClassificationPlugin(get_ai_config())
                if ai_plugin.start():
                    # Get AI column mapping
                    headers = df.columns.tolist()
                    ai_mapping_result = ai_plugin.map_columns(headers, session_id)

                    if ai_mapping_result.get('success'):
                        suggested_mapping = ai_mapping_result['suggested_mapping']
                        confidence_scores = ai_mapping_result['confidence_scores']

                        # Apply AI mappings with high confidence
                        column_renames = {}
                        for header, target_field in suggested_mapping.items():
                            confidence = confidence_scores.get(header, 0)
                            if confidence > 0.7:  # High confidence threshold
                                # Map AI fields to our expected fields
                                field_mapping = {
                                    'user_id': 'person_id',
                                    'location': 'door_id',
                                    'access_type': 'access_result'
                                }
                                final_field = field_mapping.get(target_field, target_field)
                                column_renames[header] = final_field
                                print(f"\U0001f916 AI mapped '{header}' -> '{final_field}' (confidence: {confidence:.2f})")

                        # Apply the AI-suggested renames
                        if column_renames:
                            df = df.rename(columns=column_renames)

                            # Auto-confirm high-confidence mappings
                            ai_plugin.confirm_column_mapping(suggested_mapping, session_id)

                            return df

            except ImportError:
                print("\U0001f4dd AI plugin not available, using fallback mapping")
            except Exception as e:
                print(f"\u26a0\ufe0f AI mapping failed: {e}, using fallback")

            # Fallback to simple mapping if AI fails
            fallback_mapping = {
                'user_name': 'person_id',
                'access_location': 'door_id',
                'result': 'access_result',
                'event_time': 'timestamp'
            }

            for old_col, new_col in fallback_mapping.items():
                if old_col in df.columns:
                    df = df.rename(columns={old_col: new_col})
                    print(f"\U0001f4cb Fallback mapped '{old_col}' -> '{new_col}'")

            return df

        # REST OF YOUR METHOD - apply the AI mapping first
        # Get your data...
        # data = your_data_loading_code

        # Apply AI column mapping
        # if isinstance(data, pd.DataFrame):
        #     data = apply_ai_column_mapping(data)

        # Continue with your existing analytics logic...
    
    @measure_performance("analytics.dashboard_summary", MetricType.ANALYTICS)
    @with_error_handling(ErrorCategory.ANALYTICS, ErrorSeverity.MEDIUM)
    def get_dashboard_summary(self, time_range_hours: int = 24) -> Dict[str, Any]:
        """Get comprehensive dashboard summary with enhanced metrics"""
        
        with PerformanceContext("dashboard_summary_data_fetch"):
            # Get recent access events
            cutoff_time = datetime.now() - timedelta(hours=time_range_hours)
            
            query = """
            SELECT 
                event_id, timestamp, person_id, door_id, 
                access_result, badge_status, device_status,
                door_held_open_time
            FROM access_events 
            WHERE timestamp >= %s
            ORDER BY timestamp DESC
            """
            
            events_df = self.db.execute_query(query, (cutoff_time,))
        
        if events_df.empty:
            return self._get_empty_summary()
        
        # Process data in parallel for better performance
        with PerformanceContext("dashboard_summary_processing"):
            futures = []
            
            # Basic statistics
            futures.append(
                self.thread_pool.submit(self._calculate_basic_stats, events_df)
            )
            
            # Access patterns
            futures.append(
                self.thread_pool.submit(self._analyze_access_patterns, events_df)
            )
            
            # Security metrics
            futures.append(
                self.thread_pool.submit(self._calculate_security_metrics, events_df)
            )
            
            # Trend analysis
            futures.append(
                self.thread_pool.submit(self._analyze_trends, events_df, time_range_hours)
            )
            
            # Collect results
            results = {}
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=30)
                    results.update(result)
                except Exception as e:
                    self.logger.error(f"Analytics processing error: {e}")
        
        # Add metadata
        results['metadata'] = {
            'time_range_hours': time_range_hours,
            'data_points': len(events_df),
            'last_updated': datetime.now(),
            'processing_version': '2.0'
        }
        
        return results
    
    def _calculate_basic_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate basic statistics"""
        return {
            'basic_stats': {
                'total_events': len(df),
                'unique_people': df['person_id'].nunique(),
                'unique_doors': df['door_id'].nunique(),
                'success_rate': (df['access_result'] == 'Granted').mean() * 100,
                'average_events_per_hour': len(df) / 24 if len(df) > 0 else 0,
                'most_active_door': df['door_id'].mode().iloc[0] if len(df) > 0 else None,
                'most_active_person': df['person_id'].mode().iloc[0] if len(df) > 0 else None
            }
        }
    
    def _analyze_access_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze access patterns"""
        if df.empty:
            return {'access_patterns': {}}
        
        # Convert timestamp to datetime if it's not already
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.day_name()
        
        # Hourly patterns
        hourly_counts = df['hour'].value_counts().sort_index()
        peak_hours = hourly_counts.nlargest(3).index.tolist()
        
        # Daily patterns
        daily_counts = df['day_of_week'].value_counts()
        busiest_day = daily_counts.index[0] if len(daily_counts) > 0 else None
        
        # Door usage patterns
        door_patterns = df.groupby('door_id').agg({
            'event_id': 'count',
            'access_result': lambda x: (x == 'Granted').mean() * 100
        }).round(2)
        
        return {
            'access_patterns': {
                'peak_hours': peak_hours,
                'busiest_day': busiest_day,
                'hourly_distribution': hourly_counts.to_dict(),
                'daily_distribution': daily_counts.to_dict(),
                'door_usage': door_patterns.to_dict('index'),
                'access_frequency_stats': {
                    'events_per_person': df.groupby('person_id').size().describe().to_dict(),
                    'events_per_door': df.groupby('door_id').size().describe().to_dict()
                }
            }
        }
    
    def _calculate_security_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate security-focused metrics"""
        if df.empty:
            return {'security_metrics': {}}
        
        # Failed access attempts
        failed_attempts = df[df['access_result'] == 'Denied']
        
        # Badge status issues
        invalid_badges = df[df['badge_status'] == 'Invalid']
        
        # Device status issues
        device_issues = df[df['device_status'] != 'Normal'] if 'device_status' in df.columns else pd.DataFrame()
        
        # Calculate rates
        failure_rate = len(failed_attempts) / len(df) * 100 if len(df) > 0 else 0
        invalid_badge_rate = len(invalid_badges) / len(df) * 100 if len(df) > 0 else 0
        
        # Identify potential security concerns
        security_alerts = []
        
        if failure_rate > 10:
            security_alerts.append({
                'type': 'high_failure_rate',
                'value': failure_rate,
                'description': f'High access failure rate: {failure_rate:.1f}%'
            })
        
        if invalid_badge_rate > 5:
            security_alerts.append({
                'type': 'invalid_badges',
                'value': invalid_badge_rate,
                'description': f'High invalid badge rate: {invalid_badge_rate:.1f}%'
            })
        
        # Repeated failures by person
        repeated_failures = failed_attempts.groupby('person_id').size()
        high_failure_users = repeated_failures[repeated_failures >= 3].to_dict()
        
        return {
            'security_metrics': {
                'failure_rate': round(failure_rate, 2),
                'invalid_badge_rate': round(invalid_badge_rate, 2),
                'total_failed_attempts': len(failed_attempts),
                'total_invalid_badges': len(invalid_badges),
                'device_issues': len(device_issues),
                'security_alerts': security_alerts,
                'high_failure_users': high_failure_users,
                'failed_attempts_by_door': failed_attempts['door_id'].value_counts().to_dict() if len(failed_attempts) > 0 else {}
            }
        }
    
    def _analyze_trends(self, df: pd.DataFrame, hours: int) -> Dict[str, Any]:
        """Analyze trends over time"""
        if df.empty or hours < 2:
            return {'trends': {}}
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Create time buckets for trend analysis
        bucket_size = max(1, hours // 12)  # Up to 12 data points
        df['time_bucket'] = df['timestamp'].dt.floor(f'{bucket_size}H')
        
        # Calculate trends
        trend_data = df.groupby('time_bucket').agg({
            'event_id': 'count',
            'access_result': lambda x: (x == 'Granted').mean() * 100
        }).rename(columns={'event_id': 'event_count', 'access_result': 'success_rate'})
        
        # Calculate trend direction
        if len(trend_data) >= 2:
            # Simple linear trend
            event_trend = np.polyfit(range(len(trend_data)), trend_data['event_count'], 1)[0]
            success_trend = np.polyfit(range(len(trend_data)), trend_data['success_rate'], 1)[0]
            
            event_trend_direction = 'increasing' if event_trend > 0 else 'decreasing' if event_trend < 0 else 'stable'
            success_trend_direction = 'increasing' if success_trend > 0 else 'decreasing' if success_trend < 0 else 'stable'
        else:
            event_trend_direction = 'insufficient_data'
            success_trend_direction = 'insufficient_data'
        
        return {
            'trends': {
                'event_volume_trend': event_trend_direction,
                'success_rate_trend': success_trend_direction,
                'trend_data': trend_data.to_dict('index'),
                'data_points': len(trend_data)
            }
        }
    
    @measure_performance("analytics.anomaly_detection", MetricType.ANALYTICS)
    @with_error_handling(ErrorCategory.ANALYTICS, ErrorSeverity.HIGH)
    def detect_anomalies(
        self, 
        data: pd.DataFrame, 
        sensitivity: float = 0.95,
        lookback_days: int = 30
    ) -> List[AnomalyDetection]:
        """Enhanced anomaly detection with multiple algorithms"""
        
        anomalies = []
        
        if data.empty:
            return anomalies
        
        # Ensure timestamp column is datetime
        data['timestamp'] = pd.to_datetime(data['timestamp'])
        
        # Run different anomaly detection algorithms
        with PerformanceContext("anomaly_detection_processing"):
            # Statistical anomalies
            statistical_anomalies = self._detect_statistical_anomalies(data, sensitivity)
            anomalies.extend(statistical_anomalies)
            
            # Pattern anomalies
            pattern_anomalies = self._detect_pattern_anomalies(data, lookback_days)
            anomalies.extend(pattern_anomalies)
            
            # Behavioral anomalies
            behavioral_anomalies = self._detect_behavioral_anomalies(data)
            anomalies.extend(behavioral_anomalies)
            
            # Temporal anomalies
            temporal_anomalies = self._detect_temporal_anomalies(data)
            anomalies.extend(temporal_anomalies)
        
        # Sort by confidence and timestamp
        anomalies.sort(key=lambda x: (x.confidence, x.timestamp), reverse=True)
        
        return anomalies
    
    def _detect_statistical_anomalies(self, data: pd.DataFrame, sensitivity: float) -> List[AnomalyDetection]:
        """Detect statistical outliers"""
        anomalies = []
        
        # Volume anomalies using Z-score
        if len(data) > 10:
            # Group by hour
            hourly_counts = data.set_index('timestamp').resample('1H').size()
            
            if len(hourly_counts) > 5:
                z_scores = np.abs((hourly_counts - hourly_counts.mean()) / hourly_counts.std())
                threshold = 2.5 if sensitivity > 0.9 else 2.0
                
                outlier_hours = hourly_counts[z_scores > threshold]
                
                for hour, count in outlier_hours.items():
                    anomalies.append(AnomalyDetection(
                        anomaly_id=f"STAT_{int(hour.timestamp())}",
                        anomaly_type=AnomalyType.STATISTICAL,
                        timestamp=hour,
                        confidence=min(0.95, z_scores[hour] / 3.0),
                        severity='medium' if count > hourly_counts.mean() else 'low',
                        description=f"Unusual volume: {count} events (avg: {hourly_counts.mean():.1f})",
                        affected_records=[],
                        suggested_actions=['Investigate cause of volume spike', 'Check system health'],
                        metadata={'z_score': z_scores[hour], 'count': count, 'average': hourly_counts.mean()}
                    ))
        
        return anomalies
    
    def _detect_pattern_anomalies(self, data: pd.DataFrame, lookback_days: int) -> List[AnomalyDetection]:
        """Detect pattern-based anomalies"""
        anomalies = []
        
        # Unusual time access patterns
        data['hour'] = data['timestamp'].dt.hour
        data['day_of_week'] = data['timestamp'].dt.dayofweek
        
        # Expected patterns (business hours: 8-18, weekdays)
        business_hours = set(range(8, 19))
        business_days = set(range(0, 5))  # Monday-Friday
        
        # Find after-hours access
        after_hours = data[~data['hour'].isin(business_hours)]
        weekend_access = data[~data['day_of_week'].isin(business_days)]
        
        if len(after_hours) > 0:
            for _, event in after_hours.iterrows():
                anomalies.append(AnomalyDetection(
                    anomaly_id=f"PATTERN_AH_{event['event_id']}",
                    anomaly_type=AnomalyType.PATTERN,
                    timestamp=event['timestamp'],
                    confidence=0.7,
                    severity='medium',
                    description=f"After-hours access at {event['hour']}:00",
                    affected_records=[event['event_id']],
                    suggested_actions=['Verify legitimate business need', 'Check authorization'],
                    metadata={'hour': event['hour'], 'person_id': event['person_id']}
                ))
        
        return anomalies[:10]  # Limit to prevent overwhelming
    
    def _detect_behavioral_anomalies(self, data: pd.DataFrame) -> List[AnomalyDetection]:
        """Detect behavioral anomalies"""
        anomalies = []
        
        # Multiple rapid attempts
        data_sorted = data.sort_values('timestamp')
        
        for person_id in data['person_id'].unique():
            person_data = data_sorted[data_sorted['person_id'] == person_id]
            
            if len(person_data) >= 3:
                # Check for rapid successive attempts
                time_diffs = person_data['timestamp'].diff().dt.total_seconds()
                rapid_attempts = time_diffs[time_diffs < 30]  # Less than 30 seconds
                
                if len(rapid_attempts) >= 2:
                    anomalies.append(AnomalyDetection(
                        anomaly_id=f"BEHAV_RA_{person_id}_{int(person_data.iloc[0]['timestamp'].timestamp())}",
                        anomaly_type=AnomalyType.BEHAVIORAL,
                        timestamp=person_data.iloc[0]['timestamp'],
                        confidence=0.8,
                        severity='high',
                        description=f"Rapid successive attempts by {person_id}",
                        affected_records=person_data['event_id'].tolist(),
                        suggested_actions=['Investigate user behavior', 'Check for credential issues'],
                        metadata={'person_id': person_id, 'rapid_attempts': len(rapid_attempts)}
                    ))
        
        return anomalies
    
    def _detect_temporal_anomalies(self, data: pd.DataFrame) -> List[AnomalyDetection]:
        """Detect temporal anomalies"""
        anomalies = []
        
        # Check for access during maintenance windows or holidays
        # This is a simplified example - in practice, you'd integrate with calendar systems
        
        # Check for very late night access (11 PM - 5 AM)
        data['hour'] = data['timestamp'].dt.hour
        very_late_access = data[data['hour'].isin([23, 0, 1, 2, 3, 4, 5])]
        
        for _, event in very_late_access.iterrows():
            anomalies.append(AnomalyDetection(
                anomaly_id=f"TEMP_LN_{event['event_id']}",
                anomaly_type=AnomalyType.TEMPORAL,
                timestamp=event['timestamp'],
                confidence=0.6,
                severity='low',
                description=f"Very late night access at {event['hour']}:00",
                affected_records=[event['event_id']],
                suggested_actions=['Verify work schedule', 'Check emergency protocols'],
                metadata={'hour': event['hour']}
            ))
        
        return anomalies[:5]  # Limit results
    
    @lru_cache(maxsize=128)
    @measure_performance("analytics.pattern_analysis", MetricType.ANALYTICS)
    def analyze_access_patterns(self, days: int = 30) -> Dict[str, Any]:
        """Comprehensive access pattern analysis with caching"""
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        query = """
        SELECT 
            event_id, timestamp, person_id, door_id, 
            access_result, badge_status
        FROM access_events 
        WHERE timestamp >= %s
        ORDER BY timestamp
        """
        
        data = self.db.execute_query(query, (cutoff_date,))
        
        if data.empty:
            return {'message': 'No data available for the specified period'}
        
        # Comprehensive pattern analysis
        with PerformanceContext("access_pattern_analysis"):
            analysis_result = AnalysisResult(
                analysis_type=AnalysisType.DESCRIPTIVE,
                timestamp=datetime.now(),
                data_points=len(data),
                processing_time=0,  # Will be updated
                confidence=0.95,
                results={},
                metadata={'days': days}
            )
            
            start_time = datetime.now()
            
            # Temporal patterns
            temporal_patterns = self._analyze_temporal_patterns(data)
            
            # User behavior patterns
            user_patterns = self._analyze_user_patterns(data)
            
            # Door utilization patterns
            door_patterns = self._analyze_door_patterns(data)
            
            # Security patterns
            security_patterns = self._analyze_security_patterns(data)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            analysis_result.processing_time = processing_time
            
            analysis_result.results = {
                'temporal_patterns': temporal_patterns,
                'user_patterns': user_patterns,
                'door_patterns': door_patterns,
                'security_patterns': security_patterns,
                'summary': {
                    'total_events': len(data),
                    'unique_users': data['person_id'].nunique(),
                    'unique_doors': data['door_id'].nunique(),
                    'success_rate': (data['access_result'] == 'Granted').mean() * 100,
                    'analysis_period_days': days
                }
            }
        
        return analysis_result.__dict__
    
    def _analyze_temporal_patterns(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze temporal access patterns"""
        data['timestamp'] = pd.to_datetime(data['timestamp'])
        data['hour'] = data['timestamp'].dt.hour
        data['day_of_week'] = data['timestamp'].dt.day_name()
        data['date'] = data['timestamp'].dt.date
        
        return {
            'hourly_distribution': data['hour'].value_counts().sort_index().to_dict(),
            'daily_distribution': data['day_of_week'].value_counts().to_dict(),
            'peak_hours': data['hour'].mode().tolist(),
            'busiest_days': data['day_of_week'].mode().tolist(),
            'daily_volumes': data.groupby('date').size().describe().to_dict()
        }
    
    def _analyze_user_patterns(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze user behavior patterns"""
        user_stats = data.groupby('person_id').agg({
            'event_id': 'count',
            'access_result': lambda x: (x == 'Granted').mean() * 100,
            'door_id': 'nunique'
        }).rename(columns={
            'event_id': 'total_attempts',
            'access_result': 'success_rate',
            'door_id': 'doors_accessed'
        })
        
        return {
            'most_active_users': user_stats.nlargest(10, 'total_attempts').to_dict('index'),
            'users_with_failures': user_stats[user_stats['success_rate'] < 100].to_dict('index'),
            'user_statistics': user_stats.describe().to_dict(),
            'total_unique_users': len(user_stats)
        }
    
    def _analyze_door_patterns(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze door utilization patterns"""
        door_stats = data.groupby('door_id').agg({
            'event_id': 'count',
            'person_id': 'nunique',
            'access_result': lambda x: (x == 'Granted').mean() * 100
        }).rename(columns={
            'event_id': 'total_events',
            'person_id': 'unique_users',
            'access_result': 'success_rate'
        })
        
        return {
            'busiest_doors': door_stats.nlargest(10, 'total_events').to_dict('index'),
            'doors_with_issues': door_stats[door_stats['success_rate'] < 95].to_dict('index'),
            'door_statistics': door_stats.describe().to_dict(),
            'total_doors': len(door_stats)
        }
    
    def _analyze_security_patterns(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze security-related patterns"""
        failed_attempts = data[data['access_result'] == 'Denied']
        
        security_issues = {
            'total_failed_attempts': len(failed_attempts),
            'failure_rate': len(failed_attempts) / len(data) * 100 if len(data) > 0 else 0,
            'users_with_multiple_failures': failed_attempts.groupby('person_id').size()[
                failed_attempts.groupby('person_id').size() >= 3
            ].to_dict(),
            'doors_with_high_failures': failed_attempts.groupby('door_id').size().nlargest(5).to_dict()
        }
        
        return security_issues
    
    def _get_empty_summary(self) -> Dict[str, Any]:
        """Return empty summary when no data available"""
        return {
            'basic_stats': {
                'total_events': 0,
                'unique_people': 0,
                'unique_doors': 0,
                'success_rate': 0,
                'message': 'No data available for the specified time range'
            },
            'metadata': {
                'last_updated': datetime.now(),
                'data_points': 0
            }
        }
    
    def __del__(self):
        """Cleanup thread pool on destruction"""
        if hasattr(self, 'thread_pool'):
            self.thread_pool.shutdown(wait=True)