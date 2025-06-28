"""
Anomaly Detection Analytics Module
Advanced anomaly detection using multiple algorithms and techniques
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
import logging
from scipy import stats
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.svm import OneClassSVM
import warnings
warnings.filterwarnings('ignore')

@dataclass
class Anomaly:
    """Anomaly data structure"""
    anomaly_id: str
    anomaly_type: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    confidence: float  # 0-1
    description: str
    affected_entities: List[str]
    timestamp: datetime
    context: Dict[str, Any]
    recommended_action: str

class AnomalyDetector:
    """Advanced anomaly detection with multiple algorithms"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.scaler = StandardScaler()
        
    def detect_anomalies(self, df: pd.DataFrame, 
                         sensitivity: float = 0.95) -> Dict[str, Any]:
        """Main anomaly detection function using multiple approaches"""
        try:
            if df.empty:
                return self._empty_result()
            
            df = self._prepare_data(df)
            
            anomalies = {
                'statistical_anomalies': self._detect_statistical_anomalies(df, sensitivity),
                'temporal_anomalies': self._detect_temporal_anomalies(df),
                'behavioral_anomalies': self._detect_behavioral_anomalies(df),
                'security_anomalies': self._detect_security_anomalies(df),
                'pattern_anomalies': self._detect_pattern_anomalies(df),
                'machine_learning_anomalies': self._detect_ml_anomalies(df, sensitivity),
                'anomaly_summary': {},
                'risk_assessment': {}
            }
            
            # Generate comprehensive summary
            all_anomalies = self._consolidate_anomalies(anomalies)
            anomalies['anomaly_summary'] = self._generate_anomaly_summary(all_anomalies)
            anomalies['risk_assessment'] = self._assess_overall_risk(all_anomalies)
            
            return anomalies
            
        except Exception as e:
            self.logger.error(f"Anomaly detection failed: {e}")
            return self._empty_result()
    
    def _prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare and validate data for anomaly detection"""
        df = df.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
        df['hour'] = df['timestamp'].dt.hour
        df['minute'] = df['timestamp'].dt.minute
        df['day_of_week'] = df['timestamp'].dt.day_name()
        df['is_weekend'] = df['timestamp'].dt.weekday >= 5
        df['is_business_hours'] = (df['hour'] >= 8) & (df['hour'] <= 18)
        df['time_of_day'] = df['hour'] + df['minute'] / 60.0
        
        # Sort by timestamp for sequential analysis
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        return df
    
    def _detect_statistical_anomalies(self, df: pd.DataFrame, 
                                      sensitivity: float) -> List[Dict[str, Any]]:
        """Detect anomalies using statistical methods"""
        
        anomalies = []
        
        # Volume anomalies (Z-score based)
        daily_volumes = df.groupby('date')['event_id'].count()
        if len(daily_volumes) > 2:
            z_scores = np.abs(stats.zscore(daily_volumes))
            threshold = stats.norm.ppf(sensitivity)
            
            for date, z_score in zip(daily_volumes.index, z_scores):
                if z_score > threshold:
                    anomalies.append({
                        'type': 'volume_anomaly',
                        'severity': 'high' if z_score > 3 else 'medium',
                        'confidence': min(0.99, z_score / 4),
                        'date': str(date),
                        'volume': daily_volumes[date],
                        'z_score': z_score,
                        'description': f'Unusual daily volume: {daily_volumes[date]} events (z-score: {z_score:.2f})'
                    })
        
        # Success rate anomalies
        daily_success_rates = df.groupby('date').agg({
            'access_result': lambda x: (x == 'Granted').mean()
        })['access_result']
        
        if len(daily_success_rates) > 2:
            sr_z_scores = np.abs(stats.zscore(daily_success_rates))
            sr_threshold = stats.norm.ppf(sensitivity)
            
            for date, z_score in zip(daily_success_rates.index, sr_z_scores):
                if z_score > sr_threshold and daily_success_rates[date] < 0.8:
                    anomalies.append({
                        'type': 'success_rate_anomaly',
                        'severity': 'critical' if daily_success_rates[date] < 0.5 else 'high',
                        'confidence': min(0.99, z_score / 4),
                        'date': str(date),
                        'success_rate': daily_success_rates[date],
                        'z_score': z_score,
                        'description': f'Unusually low success rate: {daily_success_rates[date]*100:.1f}%'
                    })
        
        # User activity anomalies
        user_activity = df.groupby('person_id')['event_id'].count()
        if len(user_activity) > 2:
            user_z_scores = np.abs(stats.zscore(user_activity))
            user_threshold = stats.norm.ppf(sensitivity)
            
            # Focus on unusually high activity (potential security risk)
            high_activity_users = user_activity[user_z_scores > user_threshold]
            for user_id, activity in high_activity_users.items():
                z_score = user_z_scores[user_id]
                anomalies.append({
                    'type': 'user_activity_anomaly',
                    'severity': 'high' if z_score > 3 else 'medium',
                    'confidence': min(0.99, z_score / 4),
                    'user_id': user_id,
                    'activity_count': activity,
                    'z_score': z_score,
                    'description': f'User {user_id} has unusually high activity: {activity} events'
                })
        
        return anomalies
    
    def _detect_temporal_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect temporal pattern anomalies"""
        
        anomalies = []
        
        # After-hours access spikes
        after_hours_daily = df[~df['is_business_hours']].groupby('date')['event_id'].count()
        if len(after_hours_daily) > 0:
            avg_after_hours = after_hours_daily.mean()
            std_after_hours = after_hours_daily.std()
            
            for date, count in after_hours_daily.items():
                if count > avg_after_hours + 2 * std_after_hours and count > 10:
                    anomalies.append({
                        'type': 'after_hours_spike',
                        'severity': 'high',
                        'confidence': 0.85,
                        'date': str(date),
                        'after_hours_count': count,
                        'description': f'Unusual after-hours activity on {date}: {count} events'
                    })
        
        # Weekend activity anomalies
        weekend_activity = df[df['is_weekend']].groupby('date')['event_id'].count()
        if len(weekend_activity) > 0:
            avg_weekend = weekend_activity.mean()
            
            for date, count in weekend_activity.items():
                if count > avg_weekend * 3 and count > 20:
                    anomalies.append({
                        'type': 'weekend_activity_spike',
                        'severity': 'medium',
                        'confidence': 0.75,
                        'date': str(date),
                        'weekend_count': count,
                        'description': f'High weekend activity on {date}: {count} events'
                    })
        
        # Time clustering anomalies (unusual time patterns)
        time_anomalies = self._detect_time_clustering_anomalies(df)
        anomalies.extend(time_anomalies)
        
        # Sequential time anomalies
        sequential_anomalies = self._detect_sequential_anomalies(df)
        anomalies.extend(sequential_anomalies)
        
        return anomalies
    
    def _detect_behavioral_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect behavioral pattern anomalies"""
        
        anomalies = []
        
        # Rapid repeated attempts
        df_sorted = df.sort_values(['person_id', 'timestamp'])
        df_sorted['time_diff'] = df_sorted.groupby('person_id')['timestamp'].diff()
        
        rapid_attempts = df_sorted[df_sorted['time_diff'] < pd.Timedelta(seconds=30)]
        if len(rapid_attempts) > 0:
            for user_id in rapid_attempts['person_id'].unique():
                user_rapid = rapid_attempts[rapid_attempts['person_id'] == user_id]
                anomalies.append({
                    'type': 'rapid_attempts',
                    'severity': 'high',
                    'confidence': 0.9,
                    'user_id': user_id,
                    'attempt_count': len(user_rapid),
                    'description': f'User {user_id} made {len(user_rapid)} rapid access attempts'
                })
        
        # Door hopping (multiple doors in short time)
        door_hopping_anomalies = self._detect_door_hopping(df_sorted)
        anomalies.extend(door_hopping_anomalies)
        
        # Unusual location patterns
        location_anomalies = self._detect_location_anomalies(df)
        anomalies.extend(location_anomalies)
        
        # Deviation from normal behavior patterns
        pattern_deviation_anomalies = self._detect_pattern_deviations(df)
        anomalies.extend(pattern_deviation_anomalies)
        
        return anomalies
    
    def _detect_security_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect security-specific anomalies"""
        
        anomalies = []
        
        # Failed access clustering
        failed_attempts = df[df['access_result'] == 'Denied']
        if len(failed_attempts) > 0:
            
            # Multiple failures by same user
            user_failures = failed_attempts.groupby('person_id')['event_id'].count()
            high_failure_users = user_failures[user_failures >= 5]
            
            for user_id, failure_count in high_failure_users.items():
                user_failed_data = failed_attempts[failed_attempts['person_id'] == user_id]
                doors_failed = user_failed_data['door_id'].nunique()
                
                anomalies.append({
                    'type': 'repeated_access_failures',
                    'severity': 'critical' if failure_count >= 10 else 'high',
                    'confidence': 0.95,
                    'user_id': user_id,
                    'failure_count': failure_count,
                    'doors_affected': doors_failed,
                    'description': f'User {user_id} has {failure_count} failed access attempts across {doors_failed} doors'
                })
            
            # Door-specific failure spikes
            door_failures = failed_attempts.groupby('door_id')['event_id'].count()
            for door_id, failure_count in door_failures.items():
                total_door_attempts = len(df[df['door_id'] == door_id])
                failure_rate = failure_count / total_door_attempts
                
                if failure_rate > 0.3 and failure_count >= 5:
                    anomalies.append({
                        'type': 'door_failure_spike',
                        'severity': 'high',
                        'confidence': 0.85,
                        'door_id': door_id,
                        'failure_count': failure_count,
                        'failure_rate': failure_rate,
                        'description': f'Door {door_id} has high failure rate: {failure_rate*100:.1f}% ({failure_count} failures)'
                    })
        
        # Badge status anomalies
        if 'badge_status' in df.columns:
            badge_anomalies = self._detect_badge_anomalies(df)
            anomalies.extend(badge_anomalies)
        
        # Device status anomalies
        if 'device_status' in df.columns:
            device_anomalies = self._detect_device_anomalies(df)
            anomalies.extend(device_anomalies)
        
        # Tailgating detection
        tailgating_anomalies = self._detect_tailgating(df)
        anomalies.extend(tailgating_anomalies)
        
        return anomalies
    
    def _detect_pattern_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect anomalies in access patterns"""
        
        anomalies = []
        
        # Unusual access sequences
        sequence_anomalies = self._detect_sequence_anomalies(df)
        anomalies.extend(sequence_anomalies)
        
        # Break in routine patterns
        routine_break_anomalies = self._detect_routine_breaks(df)
        anomalies.extend(routine_break_anomalies)
        
        # Frequency anomalies
        frequency_anomalies = self._detect_frequency_anomalies(df)
        anomalies.extend(frequency_anomalies)
        
        return anomalies
    
    def _detect_ml_anomalies(self, df: pd.DataFrame, 
                             sensitivity: float) -> List[Dict[str, Any]]:
        """Detect anomalies using machine learning algorithms"""
        
        anomalies = []
        
        try:
            # Prepare features for ML algorithms
            features = self._extract_ml_features(df)
            
            if len(features) < 10:  # Not enough data for ML
                return anomalies
            
            # Isolation Forest
            isolation_anomalies = self._isolation_forest_detection(features, sensitivity)
            anomalies.extend(isolation_anomalies)
            
            # One-Class SVM
            svm_anomalies = self._oneclass_svm_detection(features, sensitivity)
            anomalies.extend(svm_anomalies)
            
        except Exception as e:
            self.logger.warning(f"ML anomaly detection failed: {e}")
        
        return anomalies
    
    def _extract_ml_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract features for machine learning anomaly detection"""
        
        # Aggregate features by time windows (hourly)
        df['hour_window'] = df['timestamp'].dt.floor('H')
        
        features = df.groupby('hour_window').agg({
            'event_id': 'count',
            'person_id': 'nunique',
            'door_id': 'nunique',
            'access_result': lambda x: (x == 'Granted').mean(),
            'hour': 'mean',
            'is_weekend': 'mean',
            'is_business_hours': 'mean'
        })
        
        # Add temporal features
        features['hour_sin'] = np.sin(2 * np.pi * features['hour'] / 24)
        features['hour_cos'] = np.cos(2 * np.pi * features['hour'] / 24)
        
        # Add lag features
        features['event_count_lag1'] = features['event_id'].shift(1)
        features['success_rate_lag1'] = features['access_result'].shift(1)
        
        # Fill missing values
        features = features.fillna(features.mean())
        
        return features
    
    def _isolation_forest_detection(self, features: pd.DataFrame, 
                                    sensitivity: float) -> List[Dict[str, Any]]:
        """Detect anomalies using Isolation Forest"""
        
        anomalies = []
        
        # Configure contamination based on sensitivity
        contamination = 1 - sensitivity
        
        # Fit Isolation Forest
        iso_forest = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        
        # Scale features
        features_scaled = self.scaler.fit_transform(features)
        
        # Predict anomalies
        predictions = iso_forest.fit_predict(features_scaled)
        anomaly_scores = iso_forest.decision_function(features_scaled)
        
        # Extract anomalies
        anomaly_indices = np.where(predictions == -1)[0]
        
        for idx in anomaly_indices:
            timestamp = features.index[idx]
            score = anomaly_scores[idx]
            confidence = min(0.99, abs(score) / 2)  # Normalize score to confidence
            
            anomalies.append({
                'type': 'ml_isolation_forest',
                'severity': 'medium',
                'confidence': confidence,
                'timestamp': timestamp,
                'anomaly_score': score,
                'description': f'Isolation Forest detected anomaly at {timestamp}'
            })
        
        return anomalies
    
    def _oneclass_svm_detection(self, features: pd.DataFrame, 
                                sensitivity: float) -> List[Dict[str, Any]]:
        """Detect anomalies using One-Class SVM"""
        
        anomalies = []
        
        try:
            # Configure nu parameter based on sensitivity
            nu = 1 - sensitivity
            
            # Fit One-Class SVM
            svm = OneClassSVM(nu=nu, kernel='rbf', gamma='scale')
            
            # Scale features
            features_scaled = self.scaler.fit_transform(features)
            
            # Predict anomalies
            predictions = svm.fit_predict(features_scaled)
            
            # Extract anomalies
            anomaly_indices = np.where(predictions == -1)[0]
            
            for idx in anomaly_indices:
                timestamp = features.index[idx]
                
                anomalies.append({
                    'type': 'ml_oneclass_svm',
                    'severity': 'medium',
                    'confidence': 0.8,
                    'timestamp': timestamp,
                    'description': f'One-Class SVM detected anomaly at {timestamp}'
                })
        
        except Exception as e:
            self.logger.warning(f"One-Class SVM detection failed: {e}")
        
        return anomalies
    
    # Helper methods for specific anomaly types
    
    def _detect_time_clustering_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect unusual time clustering patterns"""
        
        anomalies = []
        
        # Look for unusual clustering of events in short time windows
        df['time_window'] = df['timestamp'].dt.floor('15min')
        window_counts = df.groupby('time_window')['event_id'].count()
        
        # Statistical threshold
        if len(window_counts) > 10:
            threshold = window_counts.mean() + 3 * window_counts.std()
            
            unusual_windows = window_counts[window_counts > threshold]
            for window, count in unusual_windows.items():
                anomalies.append({
                    'type': 'time_clustering',
                    'severity': 'medium',
                    'confidence': 0.75,
                    'time_window': window,
                    'event_count': count,
                    'description': f'Unusual clustering of {count} events in 15-minute window at {window}'
                })
        
        return anomalies
    
    def _detect_sequential_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect sequential pattern anomalies"""
        
        anomalies = []
        
        # Look for unusual gaps in sequential access
        df_sorted = df.sort_values('timestamp')
        df_sorted['time_gap'] = df_sorted['timestamp'].diff()
        
        # Very large gaps (potential system issues)
        large_gaps = df_sorted[df_sorted['time_gap'] > pd.Timedelta(hours=6)]
        for _, row in large_gaps.iterrows():
            anomalies.append({
                'type': 'sequential_gap',
                'severity': 'low',
                'confidence': 0.6,
                'gap_duration': row['time_gap'],
                'timestamp': row['timestamp'],
                'description': f'Large time gap in access sequence: {row["time_gap"]}'
            })
        
        return anomalies
    
    def _detect_door_hopping(self, df_sorted: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect door hopping behavior"""
        
        anomalies = []
        
        # Look for rapid movement between different doors
        for user_id in df_sorted['person_id'].unique():
            user_data = df_sorted[df_sorted['person_id'] == user_id].copy()
            user_data['door_change'] = user_data['door_id'] != user_data['door_id'].shift()
            user_data['time_diff'] = user_data['timestamp'].diff()
            
            # Rapid door changes (< 5 minutes)
            rapid_changes = user_data[
                (user_data['door_change']) & 
                (user_data['time_diff'] < pd.Timedelta(minutes=5))
            ]
            
            if len(rapid_changes) > 3:  # More than 3 rapid door changes
                anomalies.append({
                    'type': 'door_hopping',
                    'severity': 'medium',
                    'confidence': 0.8,
                    'user_id': user_id,
                    'rapid_changes': len(rapid_changes),
                    'description': f'User {user_id} showed door hopping behavior with {len(rapid_changes)} rapid door changes'
                })
        
        return anomalies
    
    def _detect_location_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect unusual location access patterns"""
        
        anomalies = []
        
        # Users accessing unusual number of doors
        user_door_counts = df.groupby('person_id')['door_id'].nunique()
        
        # Statistical threshold for high door diversity
        if len(user_door_counts) > 1:
            threshold = user_door_counts.mean() + 2 * user_door_counts.std()
            
            high_diversity_users = user_door_counts[user_door_counts > threshold]
            for user_id, door_count in high_diversity_users.items():
                anomalies.append({
                    'type': 'high_location_diversity',
                    'severity': 'low',
                    'confidence': 0.7,
                    'user_id': user_id,
                    'door_count': door_count,
                    'description': f'User {user_id} accessed unusually high number of doors: {door_count}'
                })
        
        return anomalies
    
    def _detect_pattern_deviations(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect deviations from established patterns"""
        
        anomalies = []
        
        # For each user, compare recent behavior to historical
        for user_id in df['person_id'].unique():
            user_data = df[df['person_id'] == user_id].sort_values('timestamp')
            
            if len(user_data) < 10:  # Need sufficient data
                continue
            
            # Split into historical and recent
            split_point = int(len(user_data) * 0.7)
            historical = user_data.iloc[:split_point]
            recent = user_data.iloc[split_point:]
            
            if len(recent) < 3:
                continue
            
            # Compare hour patterns
            hist_hours = historical['hour'].value_counts(normalize=True)
            recent_hours = recent['hour'].value_counts(normalize=True)
            
            # Calculate pattern similarity (using Hellinger distance)
            similarity = self._calculate_pattern_similarity(hist_hours, recent_hours)
            
            if similarity < 0.5:  # Significant pattern change
                anomalies.append({
                    'type': 'pattern_deviation',
                    'severity': 'medium',
                    'confidence': 0.75,
                    'user_id': user_id,
                    'similarity_score': similarity,
                    'description': f'User {user_id} showed significant deviation from historical patterns'
                })
        
        return anomalies
    
    def _detect_badge_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect badge-related anomalies"""
        
        anomalies = []
        
        invalid_badge_events = df[df['badge_status'] != 'Valid']
        
        if len(invalid_badge_events) > 0:
            # High rate of invalid badges
            invalid_rate = len(invalid_badge_events) / len(df)
            
            if invalid_rate > 0.1:  # More than 10% invalid
                anomalies.append({
                    'type': 'high_invalid_badge_rate',
                    'severity': 'high',
                    'confidence': 0.9,
                    'invalid_rate': invalid_rate,
                    'invalid_count': len(invalid_badge_events),
                    'description': f'High rate of invalid badge usage: {invalid_rate*100:.1f}%'
                })
            
            # Users with frequent invalid badge usage
            user_invalid_counts = invalid_badge_events.groupby('person_id')['event_id'].count()
            frequent_invalid_users = user_invalid_counts[user_invalid_counts >= 3]
            
            for user_id, count in frequent_invalid_users.items():
                anomalies.append({
                    'type': 'frequent_invalid_badge',
                    'severity': 'medium',
                    'confidence': 0.85,
                    'user_id': user_id,
                    'invalid_count': count,
                    'description': f'User {user_id} has frequent invalid badge usage: {count} instances'
                })
        
        return anomalies
    
    def _detect_device_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect device status anomalies"""
        
        anomalies = []
        
        device_issues = df[df['device_status'] != 'normal']
        
        if len(device_issues) > 0:
            # Group by door to find problematic devices
            door_device_issues = device_issues.groupby('door_id').agg({
                'event_id': 'count',
                'device_status': lambda x: list(x.unique())
            })
            
            for door_id, row in door_device_issues.iterrows():
                if row['event_id'] >= 3:  # Multiple device issues
                    anomalies.append({
                        'type': 'device_malfunction',
                        'severity': 'medium',
                        'confidence': 0.8,
                        'door_id': door_id,
                        'issue_count': row['event_id'],
                        'device_statuses': row['device_status'],
                        'description': f'Device at door {door_id} showing issues: {row["event_id"]} events with status {row["device_status"]}'
                    })
        
        return anomalies
    
    def _detect_tailgating(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect potential tailgating events"""
        
        anomalies = []
        
        # Look for multiple successful accesses at same door within short time
        df_sorted = df.sort_values(['door_id', 'timestamp'])
        
        for door_id in df['door_id'].unique():
            door_data = df_sorted[df_sorted['door_id'] == door_id]
            granted_access = door_data[door_data['access_result'] == 'Granted']
            
            if len(granted_access) < 2:
                continue
            
            granted_access = granted_access.copy()
            granted_access['time_diff'] = granted_access['timestamp'].diff()
            
            # Multiple accesses within 30 seconds
            rapid_accesses = granted_access[granted_access['time_diff'] < pd.Timedelta(seconds=30)]
            
            if len(rapid_accesses) > 0:
                for _, row in rapid_accesses.iterrows():
                    anomalies.append({
                        'type': 'potential_tailgating',
                        'severity': 'medium',
                        'confidence': 0.6,
                        'door_id': door_id,
                        'timestamp': row['timestamp'],
                        'time_gap': row['time_diff'],
                        'description': f'Potential tailgating at door {door_id}: access {row["time_diff"]} after previous'
                    })
        
        return anomalies
    
    def _detect_sequence_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect unusual access sequences"""
        
        anomalies = []
        
        # Analyze door access sequences for each user
        for user_id in df['person_id'].unique():
            user_data = df[df['person_id'] == user_id].sort_values('timestamp')
            
            if len(user_data) < 3:
                continue
            
            # Look for impossible sequences (e.g., being at two distant doors too quickly)
            # This would require door location data, so we'll use a simple heuristic
            user_data = user_data.copy()
            user_data['door_change'] = user_data['door_id'] != user_data['door_id'].shift()
            user_data['time_diff'] = user_data['timestamp'].diff()
            
            # Very rapid door changes (< 1 minute) might be suspicious
            rapid_sequences = user_data[
                (user_data['door_change']) & 
                (user_data['time_diff'] < pd.Timedelta(minutes=1))
            ]
            
            if len(rapid_sequences) > 2:
                anomalies.append({
                    'type': 'rapid_sequence',
                    'severity': 'low',
                    'confidence': 0.5,
                    'user_id': user_id,
                    'sequence_count': len(rapid_sequences),
                    'description': f'User {user_id} has rapid door sequence changes'
                })
        
        return anomalies
    
    def _detect_routine_breaks(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect breaks in routine patterns"""
        
        anomalies = []
        
        # This is a simplified version - in practice, you'd need more sophisticated pattern analysis
        for user_id in df['person_id'].unique():
            user_data = df[df['person_id'] == user_id]
            
            if len(user_data) < 7:  # Need at least a week of data
                continue
            
            # Check for sudden changes in daily activity level
            daily_activity = user_data.groupby('date')['event_id'].count()
            
            if len(daily_activity) > 3:
                recent_avg = daily_activity.tail(3).mean()
                historical_avg = daily_activity.head(-3).mean()
                
                # Significant change in activity level
                if abs(recent_avg - historical_avg) > historical_avg:
                    change_type = 'increase' if recent_avg > historical_avg else 'decrease'
                    anomalies.append({
                        'type': 'routine_break',
                        'severity': 'low',
                        'confidence': 0.6,
                        'user_id': user_id,
                        'change_type': change_type,
                        'historical_avg': historical_avg,
                        'recent_avg': recent_avg,
                        'description': f'User {user_id} shows {change_type} in activity level'
                    })
        
        return anomalies
    
    def _detect_frequency_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect frequency-based anomalies"""
        
        anomalies = []
        
        # Sudden burst of activity
        df['hour_window'] = df['timestamp'].dt.floor('H')
        hourly_counts = df.groupby(['person_id', 'hour_window'])['event_id'].count()
        
        # Find users with unusually high activity in single hours
        for (user_id, hour_window), count in hourly_counts.items():
            user_hourly_avg = hourly_counts[user_id].mean()
            
            if count > user_hourly_avg * 5 and count > 10:  # 5x average and at least 10 events
                anomalies.append({
                    'type': 'activity_burst',
                    'severity': 'medium',
                    'confidence': 0.7,
                    'user_id': user_id,
                    'hour_window': hour_window,
                    'event_count': count,
                    'avg_hourly': user_hourly_avg,
                    'description': f'User {user_id} had activity burst: {count} events in hour {hour_window}'
                })
        
        return anomalies
    
    def _calculate_pattern_similarity(self, pattern1: pd.Series, 
                                      pattern2: pd.Series) -> float:
        """Calculate similarity between two patterns using Hellinger distance"""
        
        # Align indices
        all_indices = pattern1.index.union(pattern2.index)
        p1 = pattern1.reindex(all_indices, fill_value=0)
        p2 = pattern2.reindex(all_indices, fill_value=0)
        
        # Calculate Hellinger distance
        hellinger = np.sqrt(0.5 * np.sum((np.sqrt(p1) - np.sqrt(p2)) ** 2))
        
        # Convert to similarity (1 - distance)
        similarity = 1 - hellinger
        
        return max(0, similarity)
    
    def _consolidate_anomalies(self, anomaly_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Consolidate all anomalies into a single list"""
        
        all_anomalies = []
        
        for category, anomalies in anomaly_dict.items():
            if category in ['anomaly_summary', 'risk_assessment']:
                continue
            
            if isinstance(anomalies, list):
                for anomaly in anomalies:
                    anomaly['category'] = category
                    all_anomalies.append(anomaly)
        
        return all_anomalies
    
    def _generate_anomaly_summary(self, all_anomalies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive anomaly summary"""
        
        if not all_anomalies:
            return {
                'total_anomalies': 0,
                'severity_breakdown': {},
                'type_breakdown': {},
                'confidence_stats': {},
                'top_anomalies': []
            }
        
        # Severity breakdown
        severity_counts = {}
        for anomaly in all_anomalies:
            severity = anomaly.get('severity', 'unknown')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Type breakdown
        type_counts = {}
        for anomaly in all_anomalies:
            anomaly_type = anomaly.get('type', 'unknown')
            type_counts[anomaly_type] = type_counts.get(anomaly_type, 0) + 1
        
        # Confidence statistics
        confidences = [anomaly.get('confidence', 0) for anomaly in all_anomalies]
        confidence_stats = {
            'mean': np.mean(confidences),
            'median': np.median(confidences),
            'min': np.min(confidences),
            'max': np.max(confidences)
        }
        
        # Top anomalies by severity and confidence
        sorted_anomalies = sorted(
            all_anomalies,
            key=lambda x: (
                {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}.get(x.get('severity', 'low'), 1),
                x.get('confidence', 0)
            ),
            reverse=True
        )
        
        top_anomalies = sorted_anomalies[:10]  # Top 10
        
        return {
            'total_anomalies': len(all_anomalies),
            'severity_breakdown': severity_counts,
            'type_breakdown': type_counts,
            'confidence_stats': confidence_stats,
            'top_anomalies': top_anomalies
        }
    
    def _assess_overall_risk(self, all_anomalies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess overall risk based on detected anomalies"""
        
        if not all_anomalies:
            return {
                'risk_level': 'low',
                'risk_score': 0,
                'risk_factors': [],
                'recommendations': []
            }
        
        # Calculate risk score
        risk_score = 0
        risk_factors = []
        
        # Severity-based scoring
        severity_weights = {'critical': 10, 'high': 5, 'medium': 2, 'low': 1}
        for anomaly in all_anomalies:
            severity = anomaly.get('severity', 'low')
            confidence = anomaly.get('confidence', 0.5)
            risk_score += severity_weights[severity] * confidence
        
        # Normalize risk score
        max_possible_score = len(all_anomalies) * 10  # All critical with full confidence
        normalized_risk_score = min(100, (risk_score / max_possible_score) * 100) if max_possible_score > 0 else 0
        
        # Determine risk level
        if normalized_risk_score >= 70:
            risk_level = 'critical'
        elif normalized_risk_score >= 50:
            risk_level = 'high'
        elif normalized_risk_score >= 25:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        # Identify key risk factors
        critical_anomalies = [a for a in all_anomalies if a.get('severity') == 'critical']
        high_anomalies = [a for a in all_anomalies if a.get('severity') == 'high']
        
        if critical_anomalies:
            risk_factors.append(f"{len(critical_anomalies)} critical security anomalies detected")
        if high_anomalies:
            risk_factors.append(f"{len(high_anomalies)} high-severity anomalies detected")
        
        # Generate recommendations
        recommendations = self._generate_risk_recommendations(all_anomalies, risk_level)
        
        return {
            'risk_level': risk_level,
            'risk_score': normalized_risk_score,
            'risk_factors': risk_factors,
            'recommendations': recommendations,
            'anomaly_impact_analysis': self._analyze_anomaly_impact(all_anomalies)
        }
    
    def _generate_risk_recommendations(self, all_anomalies: List[Dict[str, Any]], 
                                       risk_level: str) -> List[str]:
        """Generate risk mitigation recommendations"""
        
        recommendations = []
        
        # Type-specific recommendations
        anomaly_types = set(anomaly.get('type', '') for anomaly in all_anomalies)
        
        if 'repeated_access_failures' in anomaly_types:
            recommendations.append("Investigate users with repeated access failures for potential security threats")
        
        if 'rapid_attempts' in anomaly_types:
            recommendations.append("Review rapid access attempts for possible unauthorized access attempts")
        
        if 'after_hours_spike' in anomaly_types:
            recommendations.append("Implement additional monitoring for after-hours access activities")
        
        if 'door_failure_spike' in anomaly_types:
            recommendations.append("Check door hardware and access control systems for malfunctions")
        
        if 'high_invalid_badge_rate' in anomaly_types:
            recommendations.append("Review badge management procedures and user training")
        
        # Risk level specific recommendations
        if risk_level in ['critical', 'high']:
            recommendations.append("Conduct immediate security audit and review")
            recommendations.append("Consider temporary access restrictions for high-risk users")
        
        if risk_level == 'critical':
            recommendations.append("Alert security team immediately for urgent investigation")
        
        return recommendations
    
    def _analyze_anomaly_impact(self, all_anomalies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the impact of detected anomalies"""
        
        # Affected entities
        affected_users = set()
        affected_doors = set()
        
        for anomaly in all_anomalies:
            if 'user_id' in anomaly:
                affected_users.add(anomaly['user_id'])
            if 'door_id' in anomaly:
                affected_doors.add(anomaly['door_id'])
        
        # Temporal impact
        anomaly_dates = []
        for anomaly in all_anomalies:
            if 'date' in anomaly:
                anomaly_dates.append(anomaly['date'])
            elif 'timestamp' in anomaly:
                if isinstance(anomaly['timestamp'], str):
                    anomaly_dates.append(anomaly['timestamp'][:10])  # Extract date part
        
        unique_dates = len(set(anomaly_dates))
        
        return {
            'affected_users_count': len(affected_users),
            'affected_doors_count': len(affected_doors),
            'affected_dates_count': unique_dates,
            'security_impact_level': self._calculate_security_impact(all_anomalies)
        }
    
    def _calculate_security_impact(self, all_anomalies: List[Dict[str, Any]]) -> str:
        """Calculate the security impact level"""
        
        security_types = [
            'repeated_access_failures',
            'door_failure_spike',
            'high_invalid_badge_rate',
            'rapid_attempts',
            'potential_tailgating'
        ]
        
        security_anomalies = [a for a in all_anomalies if a.get('type') in security_types]
        critical_security = [a for a in security_anomalies if a.get('severity') == 'critical']
        
        if len(critical_security) >= 3:
            return 'severe'
        elif len(security_anomalies) >= 5:
            return 'significant'
        elif len(security_anomalies) >= 2:
            return 'moderate'
        else:
            return 'minimal'
    
    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result structure"""
        return {
            'statistical_anomalies': [],
            'temporal_anomalies': [],
            'behavioral_anomalies': [],
            'security_anomalies': [],
            'pattern_anomalies': [],
            'machine_learning_anomalies': [],
            'anomaly_summary': {
                'total_anomalies': 0,
                'severity_breakdown': {},
                'type_breakdown': {}
            },
            'risk_assessment': {
                'risk_level': 'low',
                'risk_score': 0,
                'risk_factors': []
            }
        }

# Factory function
def create_anomaly_detector() -> AnomalyDetector:
    """Create anomaly detector instance"""
    return AnomalyDetector()

# Export
__all__ = ['AnomalyDetector', 'Anomaly', 'create_anomaly_detector']
