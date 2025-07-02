"""
Enhanced Anomaly Detection Module
Replace the entire content of analytics/anomaly_detection.py with this code
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from scipy import stats
import logging
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

@dataclass
class AnomalyAnalysis:
    """Comprehensive anomaly analysis result"""
    total_anomalies: int
    severity_distribution: Dict[str, int]
    detection_summary: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    recommendations: List[str]

class AnomalyDetector:
    """Enhanced anomaly detector using multiple algorithms and statistical methods"""
    
    def __init__(self,
                 contamination: float = 0.1,
                 sensitivity: float = 0.95,
                 logger: Optional[logging.Logger] = None):
        self.contamination = contamination
        self.sensitivity = sensitivity
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize ML models
        self.isolation_forest = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        self.scaler = StandardScaler()
    
    def detect_anomalies(self, df: pd.DataFrame, sensitivity: Optional[float] = None) -> Dict[str, Any]:
        """Main anomaly detection method with legacy compatibility"""
        try:
            result = self.analyze_anomalies(df, sensitivity)
            return self._convert_to_legacy_format(result)
        except Exception as e:
            self.logger.error(f"Anomaly detection failed: {e}")
            return self._empty_legacy_result()
    
    def analyze_anomalies(self, df: pd.DataFrame, sensitivity: Optional[float] = None) -> AnomalyAnalysis:
        """Enhanced anomaly detection method"""
        try:
            # Use provided sensitivity or default
            detection_sensitivity = sensitivity or self.sensitivity
            
            # Prepare data for anomaly detection
            df_clean = self._prepare_anomaly_data(df)
            
            if len(df_clean) < 10:
                return self._insufficient_data_result()
            
            # Multi-method anomaly detection
            all_anomalies = []
            
            # Statistical anomaly detection
            statistical_anomalies = self._detect_statistical_anomalies(df_clean, detection_sensitivity)
            all_anomalies.extend(statistical_anomalies)
            
            # Pattern-based anomaly detection
            pattern_anomalies = self._detect_pattern_anomalies(df_clean, detection_sensitivity)
            all_anomalies.extend(pattern_anomalies)
            
            # ML-based anomaly detection
            ml_anomalies = self._detect_ml_anomalies(df_clean, detection_sensitivity)
            all_anomalies.extend(ml_anomalies)
            
            # Remove duplicates
            unique_anomalies = self._deduplicate_anomalies(all_anomalies)
            
            # Generate analysis summaries
            severity_distribution = self._calculate_severity_distribution(unique_anomalies)
            detection_summary = self._generate_detection_summary(unique_anomalies)
            risk_assessment = self._assess_overall_risk(unique_anomalies)
            recommendations = self._generate_recommendations(unique_anomalies, risk_assessment)
            
            return AnomalyAnalysis(
                total_anomalies=len(unique_anomalies),
                severity_distribution=severity_distribution,
                detection_summary=detection_summary,
                risk_assessment=risk_assessment,
                recommendations=recommendations
            )
            
        except Exception as e:
            self.logger.error(f"Anomaly detection failed: {e}")
            return self._empty_anomaly_analysis()
    
    def _prepare_anomaly_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare and clean data for anomaly detection"""
        df_clean = df.copy()
        
        # Handle Unicode issues
        string_columns = df_clean.select_dtypes(include=['object']).columns
        for col in string_columns:
            df_clean[col] = df_clean[col].astype(str).apply(
                lambda x: x.encode('utf-8', errors='ignore').decode('utf-8')
            )
        
        # Ensure required columns
        required_cols = ['timestamp', 'person_id', 'door_id', 'access_result']
        missing_cols = [col for col in required_cols if col not in df_clean.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Convert timestamp
        if not pd.api.types.is_datetime64_any_dtype(df_clean['timestamp']):
            df_clean['timestamp'] = pd.to_datetime(df_clean['timestamp'])
        
        # Add derived features
        df_clean['hour'] = df_clean['timestamp'].dt.hour
        df_clean['day_of_week'] = df_clean['timestamp'].dt.dayofweek
        df_clean['is_weekend'] = df_clean['day_of_week'].isin([5, 6])
        df_clean['is_after_hours'] = df_clean['hour'].isin(list(range(0, 6)) + list(range(22, 24)))
        df_clean['access_granted'] = (df_clean['access_result'] == 'Granted').astype(int)
        
        return df_clean
    
    def _detect_statistical_anomalies(self, df: pd.DataFrame, sensitivity: float) -> List[Dict[str, Any]]:
        """Detect statistical anomalies using multiple methods"""
        anomalies = []
        
        # Z-score based outlier detection
        z_score_anomalies = self._detect_zscore_anomalies(df, sensitivity)
        anomalies.extend(z_score_anomalies)
        
        # IQR outlier detection
        iqr_anomalies = self._detect_iqr_anomalies(df, sensitivity)
        anomalies.extend(iqr_anomalies)
        
        # Modified Z-score (MAD) detection
        mad_anomalies = self._detect_mad_anomalies(df, sensitivity)
        anomalies.extend(mad_anomalies)
        
        return anomalies
    
    def _detect_zscore_anomalies(self, df: pd.DataFrame, sensitivity: float) -> List[Dict[str, Any]]:
        """Detect anomalies using Z-score method"""
        anomalies = []
        
        # Threshold based on sensitivity
        z_threshold = 3.0 - (sensitivity - 0.5) * 2  # Range: 2.0 to 3.0
        
        try:
            # Analyze user access frequencies
            user_access_counts = df.groupby('person_id').size()
            
            if len(user_access_counts) < 3:
                return anomalies
                
            z_scores = np.abs(stats.zscore(user_access_counts.to_numpy()))
            
            outlier_users = user_access_counts[z_scores > z_threshold]
            
            for user_id, access_count in outlier_users.items():
                z_score = float(z_scores[user_access_counts.index == user_id].iloc[0])
                
                mean_access = user_access_counts.mean()
                anomaly_type = 'excessive_access_frequency' if access_count > mean_access else 'insufficient_access_frequency'
                
                severity = self._calculate_severity_from_zscore(z_score)
                confidence = min(0.99, (z_score - z_threshold) / z_threshold)
                
                anomalies.append({
                    'type': anomaly_type,
                    'severity': severity,
                    'confidence': confidence,
                    'description': f"User {user_id} has anomalous access frequency: {access_count} (Z-score: {z_score:.2f})",
                    'affected_entities': [user_id],
                    'evidence': {
                        'user_id': user_id,
                        'access_count': access_count,
                        'z_score': z_score,
                        'threshold': z_threshold,
                        'mean_access': mean_access
                    },
                    'timestamp': datetime.now()
                })
                
        except Exception as e:
            self.logger.warning(f"Z-score anomaly detection failed: {e}")
        
        return anomalies
    
    def _detect_iqr_anomalies(self, df: pd.DataFrame, sensitivity: float) -> List[Dict[str, Any]]:
        """Detect anomalies using Interquartile Range method"""
        anomalies = []
        
        # IQR multiplier based on sensitivity
        iqr_multiplier = 2.5 - sensitivity  # Range: 1.5 to 2.0
        
        try:
            # Daily access volume anomalies
            daily_access = df.groupby(df['timestamp'].dt.date).size()
            
            if len(daily_access) < 3:
                return anomalies
            
            Q1 = daily_access.quantile(0.25)
            Q3 = daily_access.quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - iqr_multiplier * IQR
            upper_bound = Q3 + iqr_multiplier * IQR
            
            outlier_days = daily_access[(daily_access < lower_bound) | (daily_access > upper_bound)]
            
            for date, access_count in outlier_days.items():
                anomaly_type = 'daily_access_spike' if access_count > upper_bound else 'daily_access_drop'
                
                if access_count > upper_bound:
                    deviation = (access_count - upper_bound) / max(IQR, 1)
                else:
                    deviation = (lower_bound - access_count) / max(IQR, 1)
                
                severity = self._calculate_severity_from_deviation(deviation)
                confidence = min(0.95, deviation / 3)
                
                anomalies.append({
                    'type': anomaly_type,
                    'severity': severity,
                    'confidence': confidence,
                    'description': f"Anomalous daily access volume on {date}: {access_count} events",
                    'affected_entities': [str(date)],
                    'evidence': {
                        'date': str(date),
                        'access_count': access_count,
                        'expected_range': (lower_bound, upper_bound),
                        'iqr_multiplier': iqr_multiplier,
                        'deviation': deviation
                    },
                    'timestamp': datetime.now()
                })
                
        except Exception as e:
            self.logger.warning(f"IQR anomaly detection failed: {e}")
        
        return anomalies
    
    def _detect_mad_anomalies(self, df: pd.DataFrame, sensitivity: float) -> List[Dict[str, Any]]:
        """Detect anomalies using Modified Z-score (Median Absolute Deviation)"""
        anomalies = []
        
        try:
            # MAD threshold based on sensitivity
            mad_threshold = 4.0 - (sensitivity - 0.5) * 2  # Range: 3.0 to 4.5
            
            # Analyze door usage frequencies
            door_usage = df.groupby('door_id').size()
            
            if len(door_usage) < 3:
                return anomalies
            
            # Calculate Modified Z-score using MAD
            median_usage = door_usage.median()
            mad = np.median(np.abs(door_usage - median_usage))
            
            if mad > 0:
                modified_z_scores = 0.6745 * (door_usage - median_usage) / mad
                
                outlier_doors = door_usage[np.abs(modified_z_scores) > mad_threshold]
                
                for door_id, usage_count in outlier_doors.items():
                    z_score = float(abs(modified_z_scores[door_id]))
                    
                    anomaly_type = 'door_overuse' if usage_count > median_usage else 'door_underuse'
                    severity = self._calculate_severity_from_zscore(z_score)
                    confidence = min(0.95, (z_score - mad_threshold) / mad_threshold)
                    
                    anomalies.append({
                        'type': anomaly_type,
                        'severity': severity,
                        'confidence': confidence,
                        'description': f"Door {door_id} shows anomalous usage pattern: {usage_count} events (MAD Z-score: {z_score:.2f})",
                        'affected_entities': [door_id],
                        'evidence': {
                            'door_id': door_id,
                            'usage_count': usage_count,
                            'modified_z_score': z_score,
                            'threshold': mad_threshold,
                            'median_usage': median_usage
                        },
                        'timestamp': datetime.now()
                    })
                    
        except Exception as e:
            self.logger.warning(f"MAD anomaly detection failed: {e}")
        
        return anomalies
    
    def _detect_pattern_anomalies(self, df: pd.DataFrame, sensitivity: float) -> List[Dict[str, Any]]:
        """Detect pattern-based anomalies"""
        anomalies = []
        
        # Rapid successive access attempts
        rapid_access_anomalies = self._detect_rapid_access_patterns(df, sensitivity)
        anomalies.extend(rapid_access_anomalies)
        
        # Badge status anomalies
        badge_anomalies = self._detect_badge_anomalies(df, sensitivity)
        anomalies.extend(badge_anomalies)
        
        # Time-based anomalies
        temporal_anomalies = self._detect_temporal_anomalies(df, sensitivity)
        anomalies.extend(temporal_anomalies)
        
        return anomalies
    
    def _detect_rapid_access_patterns(self, df: pd.DataFrame, sensitivity: float) -> List[Dict[str, Any]]:
        """Detect rapid successive access attempts"""
        anomalies = []
        
        # Time threshold based on sensitivity
        time_threshold = 60 - (sensitivity - 0.5) * 60  # Range: 30-60 seconds
        
        try:
            df_sorted = df.sort_values(['person_id', 'timestamp'])
            df_sorted['time_diff'] = df_sorted.groupby('person_id')['timestamp'].diff().dt.total_seconds()
            
            # Find rapid attempts
            rapid_attempts = df_sorted[df_sorted['time_diff'] < time_threshold]
            
            if len(rapid_attempts) > 0:
                user_rapid_counts = rapid_attempts.groupby('person_id').size()
                
                for user_id, count in user_rapid_counts.items():
                    if count >= 2:
                        user_rapid_data = rapid_attempts[rapid_attempts['person_id'] == user_id]
                        failure_rate = 1 - user_rapid_data['access_granted'].mean()
                        
                        severity = 'critical' if failure_rate > 0.8 else 'high' if failure_rate > 0.5 else 'medium'
                        confidence = min(0.95, count / 10)
                        
                        anomalies.append({
                            'type': 'rapid_access_attempts',
                            'severity': severity,
                            'confidence': confidence,
                            'description': f"User {user_id} made {count} rapid access attempts within {time_threshold}s",
                            'affected_entities': [user_id],
                            'evidence': {
                                'user_id': user_id,
                                'rapid_attempts': count,
                                'failure_rate': failure_rate,
                                'time_threshold': time_threshold,
                                'attempts_details': user_rapid_data[['timestamp', 'door_id', 'access_result']].to_dict('records')
                            },
                            'timestamp': datetime.now()
                        })
                        
        except Exception as e:
            self.logger.warning(f"Rapid access pattern detection failed: {e}")
        
        return anomalies
    
    def _detect_badge_anomalies(self, df: pd.DataFrame, sensitivity: float) -> List[Dict[str, Any]]:
        """Detect badge-related anomalies"""
        anomalies = []
        
        if 'badge_status' not in df.columns:
            return anomalies
        
        try:
            # High invalid badge rate per user
            user_badge_stats = df.groupby('person_id')['badge_status'].agg(['count', lambda x: (x != 'Valid').mean()])
            user_badge_stats.columns = ['total_events', 'invalid_rate']
            
            # Filter users with significant activity and high invalid rate
            problematic_users = user_badge_stats[
                (user_badge_stats['total_events'] >= 5) & 
                (user_badge_stats['invalid_rate'] > 0.2)
            ]
            
            for user_id, stats in problematic_users.iterrows():
                severity = 'critical' if stats['invalid_rate'] > 0.5 else 'high'
                confidence = min(0.95, stats['invalid_rate'])
                
                anomalies.append({
                    'type': 'high_invalid_badge_rate',
                    'severity': severity,
                    'confidence': confidence,
                    'description': f"User {user_id} has high invalid badge rate: {stats['invalid_rate']:.1%}",
                    'affected_entities': [user_id],
                    'evidence': {
                        'user_id': user_id,
                        'invalid_rate': stats['invalid_rate'],
                        'total_events': stats['total_events']
                    },
                    'timestamp': datetime.now()
                })
                
        except Exception as e:
            self.logger.warning(f"Badge anomaly detection failed: {e}")
        
        return anomalies
    
    def _detect_temporal_anomalies(self, df: pd.DataFrame, sensitivity: float) -> List[Dict[str, Any]]:
        """Detect temporal anomalies in access patterns"""
        anomalies = []
        
        try:
            # Unusual hour activity
            hour_counts = df['hour'].value_counts()
            hour_mean = hour_counts.mean()
            hour_std = hour_counts.std()
            
            if hour_std > 0:
                for hour, count in hour_counts.items():
                    z_score = abs(count - hour_mean) / hour_std
                    if z_score > 2.5:  # Significant deviation
                        anomalies.append({
                            'type': 'unusual_hour_activity',
                            'severity': 'high' if z_score > 3 else 'medium',
                            'confidence': min(0.9, z_score / 3),
                            'description': f"Unusual activity at hour {hour}: {count} events (Z-score: {z_score:.2f})",
                            'affected_entities': [f"hour_{hour}"],
                            'evidence': {
                                'hour': hour,
                                'event_count': count,
                                'z_score': z_score,
                                'mean_hourly': hour_mean,
                                'std_hourly': hour_std
                            },
                            'timestamp': datetime.now()
                        })
                        
        except Exception as e:
            self.logger.warning(f"Temporal anomaly detection failed: {e}")
        
        return anomalies
    
    def _detect_ml_anomalies(self, df: pd.DataFrame, sensitivity: float) -> List[Dict[str, Any]]:
        """Detect anomalies using machine learning methods"""
        anomalies = []
        
        try:
            # Prepare features for ML detection
            features_df = self._prepare_ml_features(df)
            
            if len(features_df) < 10:
                return anomalies
            
            # Isolation Forest detection
            isolation_anomalies = self._isolation_forest_detection(features_df, sensitivity, df)
            anomalies.extend(isolation_anomalies)
            
        except Exception as e:
            self.logger.warning(f"ML anomaly detection failed: {e}")
        
        return anomalies
    
    def _prepare_ml_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for ML-based anomaly detection"""
        
        # Event-level features
        event_features = []
        
        for idx, row in df.iterrows():
            # Temporal features
            hour_norm = row['hour'] / 24.0
            dow_norm = row['day_of_week'] / 7.0
            
            # User-based features
            user_data = df[df['person_id'] == row['person_id']]
            user_event_count = len(user_data)
            user_success_rate = user_data['access_granted'].mean()
            
            # Door-based features
            door_data = df[df['door_id'] == row['door_id']]
            door_usage_frequency = len(door_data)
            door_success_rate = door_data['access_granted'].mean()
            
            event_features.append({
                'hour_norm': hour_norm,
                'dow_norm': dow_norm,
                'is_weekend': float(row['is_weekend']),
                'is_after_hours': float(row['is_after_hours']),
                'access_granted': float(row['access_granted']),
                'user_event_count': user_event_count,
                'user_success_rate': user_success_rate,
                'door_usage_frequency': door_usage_frequency,
                'door_success_rate': door_success_rate
            })
        
        features_df = pd.DataFrame(event_features)
        features_df.index = df.index  # Maintain original index
        
        return features_df.fillna(0)
    
    def _isolation_forest_detection(self, features_df: pd.DataFrame, sensitivity: float, original_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect anomalies using Isolation Forest"""
        anomalies = []
        
        try:
            # Adjust contamination based on sensitivity
            contamination = 0.05 + (1 - sensitivity) * 0.15  # Range: 0.05 to 0.20
            
            isolation_forest = IsolationForest(
                contamination=contamination,
                random_state=42,
                n_estimators=100
            )
            
            # Scale features
            features_scaled = self.scaler.fit_transform(features_df)
            
            # Detect outliers
            outlier_predictions = isolation_forest.fit_predict(features_scaled)
            anomaly_scores = isolation_forest.decision_function(features_scaled)
            
            # Process anomalies
            anomaly_indices = np.where(outlier_predictions == -1)[0]
            
            for idx in anomaly_indices:
                original_idx = features_df.index[idx]
                anomaly_score = float(abs(anomaly_scores[idx]))
                
                # Calculate confidence
                confidence = min(0.95, anomaly_score / 2)
                
                if confidence >= 0.5:  # Only high-confidence anomalies
                    severity = self._calculate_severity_from_score(anomaly_score)
                    
                    # Get original row data
                    original_row = original_df.loc[original_idx]
                    
                    anomalies.append({
                        'type': 'ml_behavioral_anomaly',
                        'severity': severity,
                        'confidence': confidence,
                        'description': "Isolation Forest detected anomalous behavior pattern",
                        'affected_entities': [f"event_{original_idx}"],
                        'evidence': {
                            'event_index': original_idx,
                            'anomaly_score': anomaly_score,
                            'contamination': contamination,
                            'person_id': original_row['person_id'],
                            'door_id': original_row['door_id'],
                            'timestamp': original_row['timestamp'].isoformat(),
                            'features': features_df.loc[original_idx].to_dict()
                        },
                        'timestamp': datetime.now()
                    })
                    
        except Exception as e:
            self.logger.warning(f"Isolation Forest detection failed: {e}")
        
        return anomalies
    
    def _calculate_severity_from_zscore(self, z_score: float) -> str:
        """Calculate severity level from Z-score"""
        if z_score >= 4.0:
            return 'critical'
        elif z_score >= 3.5:
            return 'high'
        elif z_score >= 3.0:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_severity_from_deviation(self, deviation: float) -> str:
        """Calculate severity level from IQR deviation"""
        if deviation >= 3.0:
            return 'critical'
        elif deviation >= 2.0:
            return 'high'
        elif deviation >= 1.0:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_severity_from_score(self, score: float) -> str:
        """Calculate severity level from anomaly score"""
        if score >= 0.8:
            return 'critical'
        elif score >= 0.6:
            return 'high'
        elif score >= 0.4:
            return 'medium'
        else:
            return 'low'
    
    def _deduplicate_anomalies(self, anomalies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate and similar anomalies"""
        if not anomalies:
            return anomalies
        
        # Simple deduplication based on type and affected entities
        seen_combinations = set()
        unique_anomalies = []
        
        for anomaly in anomalies:
            # Create a key for deduplication
            entities_key = tuple(sorted(anomaly['affected_entities']))
            dedup_key = (anomaly['type'], entities_key)
            
            if dedup_key not in seen_combinations:
                seen_combinations.add(dedup_key)
                unique_anomalies.append(anomaly)
        
        return unique_anomalies
    
    def _calculate_severity_distribution(self, anomalies: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate distribution of anomalies by severity"""
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        
        for anomaly in anomalies:
            severity = anomaly.get('severity', 'low')
            severity_counts[severity] += 1
        
        return severity_counts
    
    def _generate_detection_summary(self, anomalies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate detection summary"""
        if not anomalies:
            return {'total_anomalies': 0, 'message': 'No anomalies detected'}
        
        # Type breakdown
        type_counts = {}
        for anomaly in anomalies:
            anomaly_type = anomaly.get('type', 'unknown')
            type_counts[anomaly_type] = type_counts.get(anomaly_type, 0) + 1
        
        # Confidence statistics
        confidences = [anomaly.get('confidence', 0) for anomaly in anomalies]
        
        return {
            'total_anomalies': len(anomalies),
            'type_breakdown': type_counts,
            'confidence_stats': {
                'mean': np.mean(confidences),
                'max': np.max(confidences),
                'min': np.min(confidences)
            },
            'detection_methods': list(set([a.get('type', 'unknown') for a in anomalies]))
        }
    
    def _assess_overall_risk(self, anomalies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess overall risk based on detected anomalies"""
        if not anomalies:
            return {
                'risk_level': 'low',
                'risk_score': 0,
                'risk_factors': []
            }
        
        # Calculate risk score
        risk_score = 0
        severity_weights = {'critical': 10, 'high': 5, 'medium': 2, 'low': 1}
        
        for anomaly in anomalies:
            severity = anomaly.get('severity', 'low')
            confidence = anomaly.get('confidence', 0.5)
            risk_score += severity_weights[severity] * confidence
        
        # Normalize risk score
        max_possible_score = len(anomalies) * 10
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
        
        return {
            'risk_level': risk_level,
            'risk_score': normalized_risk_score,
            'risk_factors': [a['type'] for a in anomalies if a.get('severity') in ['critical', 'high']]
        }
    
    def _generate_recommendations(self, anomalies: List[Dict[str, Any]], 
                                risk_assessment: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on anomalies"""
        recommendations = []
        
        if not anomalies:
            recommendations.append("No anomalies detected. System appears to be functioning normally.")
            return recommendations
        
        # Risk-based recommendations
        risk_level = risk_assessment.get('risk_level', 'low')
        if risk_level in ['critical', 'high']:
            recommendations.append(
                f"URGENT: {risk_level.upper()} risk level detected. "
                "Immediate investigation and response required."
            )
        
        # Type-specific recommendations
        anomaly_types = [a['type'] for a in anomalies]
        if 'rapid_access_attempts' in anomaly_types:
            recommendations.append(
                "Rapid access attempts detected. Consider implementing rate limiting "
                "and reviewing user access patterns."
            )
        
        if 'excessive_access_frequency' in anomaly_types:
            recommendations.append(
                "Users with excessive access frequency identified. "
                "Review user roles and access requirements."
            )
        
        if 'daily_access_spike' in anomaly_types:
            recommendations.append(
                "Unusual daily access spikes detected. Investigate potential system issues "
                "or security incidents."
            )
        
        if 'high_invalid_badge_rate' in anomaly_types:
            recommendations.append(
                "High invalid badge rates detected. Review badge management and replacement procedures."
            )
        
        if 'ml_behavioral_anomaly' in anomaly_types:
            recommendations.append(
                "Machine learning models detected behavioral anomalies. "
                "Review flagged events for potential security concerns."
            )
        
        # General recommendation
        if len(recommendations) == 0:
            recommendations.append("Monitor detected anomalies and investigate as needed.")
        
        return recommendations
    
    def _convert_to_legacy_format(self, result: AnomalyAnalysis) -> Dict[str, Any]:
        """Convert AnomalyAnalysis to legacy dictionary format"""
        return {
            'anomalies_detected': result.total_anomalies,
            'threat_level': result.risk_assessment.get('risk_level', 'low'),
            'severity_distribution': result.severity_distribution,
            'detection_summary': result.detection_summary,
            'risk_assessment': result.risk_assessment,
            'recommendations': result.recommendations,
            # Legacy compatibility fields
            'statistical_anomalies': [a for a in result.detection_summary.get('type_breakdown', {}).keys() if 'zscore' in a or 'iqr' in a or 'mad' in a],
            'pattern_anomalies': [a for a in result.detection_summary.get('type_breakdown', {}).keys() if 'rapid' in a or 'badge' in a],
            'ml_anomalies': [a for a in result.detection_summary.get('type_breakdown', {}).keys() if 'ml' in a],
            'anomaly_count': result.total_anomalies,
            'confidence_mean': result.detection_summary.get('confidence_stats', {}).get('mean', 0)
        }
    
    def _insufficient_data_result(self) -> AnomalyAnalysis:
        """Return result for insufficient data"""
        return AnomalyAnalysis(
            total_anomalies=0,
            severity_distribution={},
            detection_summary={'total_anomalies': 0, 'message': 'Insufficient data for anomaly detection'},
            risk_assessment={'risk_level': 'unknown', 'risk_score': 0},
            recommendations=['Collect more data for meaningful anomaly detection']
        )
    
    def _empty_anomaly_analysis(self) -> AnomalyAnalysis:
        """Return empty anomaly analysis for error cases"""
        return AnomalyAnalysis(
            total_anomalies=0,
            severity_distribution={},
            detection_summary={'total_anomalies': 0, 'message': 'Error in anomaly detection'},
            risk_assessment={'risk_level': 'error', 'risk_score': 0},
            recommendations=['Unable to perform anomaly detection due to data issues']
        )
    
    def _empty_legacy_result(self) -> Dict[str, Any]:
        """Return empty result in legacy format"""
        return {
            'anomalies_detected': 0,
            'threat_level': 'unknown',
            'severity_distribution': {},
            'detection_summary': {'total_anomalies': 0, 'message': 'Error in anomaly detection'},
            'risk_assessment': {'risk_level': 'error', 'risk_score': 0},
            'recommendations': ['Unable to perform anomaly detection due to data issues'],
            'statistical_anomalies': [],
            'pattern_anomalies': [],
            'ml_anomalies': [],
            'anomaly_count': 0,
            'confidence_mean': 0
        }

# Factory function for compatibility
def create_anomaly_detector(**kwargs) -> AnomalyDetector:
    """Factory function to create anomaly detector"""
    return AnomalyDetector(**kwargs)

# Alias for enhanced version
EnhancedAnomalyDetector = AnomalyDetector
create_enhanced_anomaly_detector = create_anomaly_detector

# Export for compatibility
__all__ = ['AnomalyDetector', 'create_anomaly_detector', 'EnhancedAnomalyDetector']