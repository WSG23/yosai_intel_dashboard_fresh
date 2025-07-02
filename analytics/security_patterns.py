"""
Enhanced Security Patterns Analyzer
Replace the entire content of analytics/security_patterns.py with this code
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from scipy import stats
import logging
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

@dataclass
class ThreatIndicator:
    """Individual threat indicator"""
    threat_type: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    confidence: float  # 0.0 to 1.0
    description: str
    evidence: Dict[str, Any]
    timestamp: datetime
    affected_entities: List[str]

@dataclass
class SecurityAssessment:
    """Comprehensive security assessment result"""
    overall_score: float  # 0-100
    risk_level: str
    confidence_interval: Tuple[float, float]
    threat_indicators: List[ThreatIndicator]
    pattern_analysis: Dict[str, Any]
    recommendations: List[str]

class SecurityPatternsAnalyzer:
    """Enhanced security patterns analyzer with ML-based threat detection"""
    
    def __init__(self, 
                 contamination: float = 0.1,
                 confidence_threshold: float = 0.7,
                 logger: Optional[logging.Logger] = None):
        self.contamination = contamination
        self.confidence_threshold = confidence_threshold
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize ML models
        self.isolation_forest = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        self.scaler = StandardScaler()
    
    def analyze_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Main analysis method with legacy compatibility"""
        try:
            result = self.analyze_security_patterns(df)
            return self._convert_to_legacy_format(result)
        except Exception as e:
            self.logger.error(f"Security analysis failed: {e}")
            return self._empty_legacy_result()
    
    def analyze_security_patterns(self, df: pd.DataFrame) -> SecurityAssessment:
        """Enhanced security analysis method"""
        try:
            df_clean = self._prepare_security_data(df)
            threat_indicators = []
            
            # Statistical anomaly detection
            statistical_threats = self._detect_statistical_threats(df_clean)
            threat_indicators.extend(statistical_threats)
            
            # Pattern-based threat detection
            pattern_threats = self._detect_pattern_threats(df_clean)
            threat_indicators.extend(pattern_threats)
            
            # Calculate overall security score
            security_score = self._calculate_comprehensive_score(df_clean, threat_indicators)
            
            # Generate pattern analysis
            pattern_analysis = self._analyze_access_patterns(df_clean)
            
            # Generate recommendations
            recommendations = self._generate_security_recommendations(threat_indicators, pattern_analysis)
            
            # Determine risk level and confidence
            risk_level = self._determine_risk_level(security_score, threat_indicators)
            confidence_interval = self._calculate_confidence_interval(df_clean, security_score)
            
            return SecurityAssessment(
                overall_score=security_score,
                risk_level=risk_level,
                confidence_interval=confidence_interval,
                threat_indicators=threat_indicators,
                pattern_analysis=pattern_analysis,
                recommendations=recommendations
            )
            
        except Exception as e:
            self.logger.error(f"Security analysis failed: {e}")
            return self._empty_security_assessment()
    
    def _prepare_security_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare and clean data for security analysis"""
        df_clean = df.copy()
        
        # Handle Unicode issues
        string_columns = df_clean.select_dtypes(include=['object']).columns
        for col in string_columns:
            df_clean[col] = df_clean[col].astype(str).apply(
                lambda x: x.encode('utf-8', errors='ignore').decode('utf-8')
            )
        
        # Ensure required columns exist
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
    
    def _detect_statistical_threats(self, df: pd.DataFrame) -> List[ThreatIndicator]:
        """Detect threats using statistical methods"""
        threats = []
        
        # Failure rate anomalies
        failure_threats = self._detect_failure_rate_anomalies(df)
        threats.extend(failure_threats)
        
        # Frequency anomalies
        frequency_threats = self._detect_frequency_anomalies(df)
        threats.extend(frequency_threats)
        
        return threats
    
    def _detect_failure_rate_anomalies(self, df: pd.DataFrame) -> List[ThreatIndicator]:
        """Detect unusual failure rate patterns"""
        threats = []
        
        try:
            # Overall failure rate
            overall_failure_rate = 1 - df['access_granted'].mean()
            
            # Per-user failure rates
            user_failure_rates = df.groupby('person_id')['access_granted'].agg(['mean', 'count'])
            user_failure_rates['failure_rate'] = 1 - user_failure_rates['mean']
            
            # Statistical outlier detection (using IQR method)
            Q1 = user_failure_rates['failure_rate'].quantile(0.25)
            Q3 = user_failure_rates['failure_rate'].quantile(0.75)
            IQR = Q3 - Q1
            outlier_threshold = Q3 + 1.5 * IQR
            
            high_failure_users = user_failure_rates[
                (user_failure_rates['failure_rate'] > outlier_threshold) & 
                (user_failure_rates['count'] >= 5)
            ]
            
            for user_id, data in high_failure_users.iterrows():
                n_attempts = data['count']
                n_failures = int(n_attempts * data['failure_rate'])
                p_value = stats.binom_test(n_failures, n_attempts, overall_failure_rate)
                
                if p_value < 0.05:
                    confidence = 1 - p_value
                    severity = 'critical' if data['failure_rate'] > 0.8 else 'high'
                    
                    threats.append(ThreatIndicator(
                        threat_type='unusual_failure_rate',
                        severity=severity,
                        confidence=confidence,
                        description=f"User {user_id} has unusually high failure rate: {data['failure_rate']:.2%}",
                        evidence={
                            'user_id': user_id,
                            'failure_rate': data['failure_rate'],
                            'attempts': n_attempts,
                            'p_value': p_value,
                            'baseline_rate': overall_failure_rate
                        },
                        timestamp=datetime.now(),
                        affected_entities=[user_id]
                    ))
        except Exception as e:
            self.logger.warning(f"Failure rate anomaly detection failed: {e}")
        
        return threats
    
    def _detect_frequency_anomalies(self, df: pd.DataFrame) -> List[ThreatIndicator]:
        """Detect unusual access frequency patterns"""
        threats = []
        
        try:
            # Access frequency per user
            user_access_counts = df.groupby('person_id').size()
            
            # Z-score based anomaly detection
            mean_access = user_access_counts.mean()
            std_access = user_access_counts.std()
            
            if std_access > 0:
                z_scores = (user_access_counts - mean_access) / std_access
                
                # High frequency anomalies (potential abuse)
                high_freq_users = user_access_counts[z_scores > 3]
                
                for user_id, access_count in high_freq_users.items():
                    confidence = min(0.99, (z_scores[user_id] - 3) / 3)
                    
                    threats.append(ThreatIndicator(
                        threat_type='excessive_access_frequency',
                        severity='medium',
                        confidence=confidence,
                        description=f"User {user_id} has excessive access frequency: {access_count} events",
                        evidence={
                            'user_id': user_id,
                            'access_count': access_count,
                            'z_score': z_scores[user_id],
                            'baseline_mean': mean_access
                        },
                        timestamp=datetime.now(),
                        affected_entities=[user_id]
                    ))
        except Exception as e:
            self.logger.warning(f"Frequency anomaly detection failed: {e}")
        
        return threats
    
    def _detect_pattern_threats(self, df: pd.DataFrame) -> List[ThreatIndicator]:
        """Detect pattern-based security threats"""
        threats = []
        
        # Rapid successive attempts
        rapid_attempts = self._detect_rapid_attempts(df)
        threats.extend(rapid_attempts)
        
        # After-hours anomalies
        after_hours_threats = self._detect_after_hours_anomalies(df)
        threats.extend(after_hours_threats)
        
        return threats
    
    def _detect_rapid_attempts(self, df: pd.DataFrame) -> List[ThreatIndicator]:
        """Detect rapid successive access attempts"""
        threats = []
        
        try:
            df_sorted = df.sort_values(['person_id', 'timestamp'])
            df_sorted['time_diff'] = df_sorted.groupby('person_id')['timestamp'].diff()
            
            # Find attempts within 30 seconds
            rapid_threshold = pd.Timedelta(seconds=30)
            rapid_attempts = df_sorted[df_sorted['time_diff'] < rapid_threshold]
            
            if len(rapid_attempts) > 0:
                user_rapid_counts = rapid_attempts.groupby('person_id').size()
                
                for user_id, count in user_rapid_counts.items():
                    if count >= 3:
                        user_rapid_data = rapid_attempts[rapid_attempts['person_id'] == user_id]
                        failure_rate = 1 - user_rapid_data['access_granted'].mean()
                        
                        severity = 'critical' if failure_rate > 0.7 else 'high'
                        confidence = min(0.95, count / 10)
                        
                        threats.append(ThreatIndicator(
                            threat_type='rapid_access_attempts',
                            severity=severity,
                            confidence=confidence,
                            description=f"User {user_id} made {count} rapid access attempts",
                            evidence={
                                'user_id': user_id,
                                'rapid_attempts': count,
                                'failure_rate': failure_rate,
                                'time_window': 'within_30_seconds'
                            },
                            timestamp=datetime.now(),
                            affected_entities=[user_id]
                        ))
        except Exception as e:
            self.logger.warning(f"Rapid attempts detection failed: {e}")
        
        return threats
    
    def _detect_after_hours_anomalies(self, df: pd.DataFrame) -> List[ThreatIndicator]:
        """Detect suspicious after-hours access patterns"""
        threats = []
        
        try:
            after_hours_data = df[df['is_after_hours'] == True]
            
            if len(after_hours_data) == 0:
                return threats
                
            # Users with excessive after-hours access
            user_after_hours = after_hours_data.groupby('person_id').size()
            
            # Statistical threshold for after-hours access
            threshold = user_after_hours.quantile(0.9)
            
            excessive_users = user_after_hours[user_after_hours > threshold]
            
            for user_id, count in excessive_users.items():
                user_total = len(df[df['person_id'] == user_id])
                after_hours_rate = count / user_total
                
                if after_hours_rate > 0.3:  # More than 30% after hours
                    threats.append(ThreatIndicator(
                        threat_type='excessive_after_hours_access',
                        severity='medium',
                        confidence=min(0.9, after_hours_rate),
                        description=f"User {user_id} has excessive after-hours access: {count} events ({after_hours_rate:.1%})",
                        evidence={
                            'user_id': user_id,
                            'after_hours_count': count,
                            'after_hours_rate': after_hours_rate,
                            'total_events': user_total
                        },
                        timestamp=datetime.now(),
                        affected_entities=[user_id]
                    ))
        except Exception as e:
            self.logger.warning(f"After-hours anomaly detection failed: {e}")
        
        return threats
    
    def _calculate_comprehensive_score(self, df: pd.DataFrame, threats: List[ThreatIndicator]) -> float:
        """Calculate comprehensive security score (0-100)"""
        base_score = 100.0
        
        # Penalty for each threat based on severity and confidence
        severity_weights = {'critical': 25, 'high': 15, 'medium': 8, 'low': 3}
        
        total_penalty = 0
        for threat in threats:
            penalty = severity_weights.get(threat.severity, 3) * threat.confidence
            total_penalty += penalty
        
        # Additional penalties for overall statistics
        failure_rate = 1 - df['access_granted'].mean()
        failure_penalty = min(30, failure_rate * 100)
        
        after_hours_rate = df['is_after_hours'].mean()
        after_hours_penalty = min(10, after_hours_rate * 50)
        
        total_penalty += failure_penalty + after_hours_penalty
        
        final_score = max(0, base_score - total_penalty)
        return round(final_score, 2)
    
    def _analyze_access_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze overall access patterns for security assessment"""
        patterns = {
            'temporal_distribution': {},
            'user_distribution': {},
            'failure_patterns': {}
        }
        
        try:
            # Temporal patterns
            hourly_dist = df['hour'].value_counts().sort_index()
            patterns['temporal_distribution'] = {
                'peak_hours': hourly_dist.nlargest(3).index.tolist(),
                'after_hours_percentage': df['is_after_hours'].mean() * 100,
                'weekend_percentage': df['is_weekend'].mean() * 100
            }
            
            # User patterns
            user_activity = df.groupby('person_id').agg({
                'event_id': 'count',
                'access_granted': 'mean'
            })
            
            patterns['user_distribution'] = {
                'total_users': len(user_activity),
                'average_events_per_user': user_activity['event_id'].mean(),
                'average_success_rate': user_activity['access_granted'].mean()
            }
            
            # Failure patterns
            failed_attempts = df[df['access_granted'] == 0]
            if len(failed_attempts) > 0:
                patterns['failure_patterns'] = {
                    'total_failures': len(failed_attempts),
                    'failure_rate': len(failed_attempts) / len(df),
                    'top_failure_users': failed_attempts['person_id'].value_counts().head(5).to_dict()
                }
            
        except Exception as e:
            self.logger.warning(f"Pattern analysis failed: {e}")
        
        return patterns
    
    def _generate_security_recommendations(self, threats: List[ThreatIndicator], 
                                         patterns: Dict[str, Any]) -> List[str]:
        """Generate security recommendations"""
        recommendations = []
        
        critical_threats = [t for t in threats if t.severity == 'critical']
        high_threats = [t for t in threats if t.severity == 'high']
        
        if critical_threats:
            recommendations.append(
                f"URGENT: {len(critical_threats)} critical security threats detected. "
                "Immediate investigation required."
            )
        
        if high_threats:
            recommendations.append(
                f"HIGH PRIORITY: {len(high_threats)} high-severity threats require attention."
            )
        
        failure_patterns = patterns.get('failure_patterns', {})
        if failure_patterns.get('failure_rate', 0) > 0.1:
            recommendations.append(
                "High failure rate detected (>10%). Review access control systems."
            )
        
        # Threat type specific recommendations
        threat_types = [t.threat_type for t in threats]
        if 'rapid_access_attempts' in threat_types:
            recommendations.append(
                "Rapid access attempts detected. Consider implementing rate limiting."
            )
        
        if 'excessive_after_hours_access' in threat_types:
            recommendations.append(
                "Excessive after-hours activity detected. Review after-hours policies."
            )
        
        if not recommendations:
            recommendations.append("No significant security issues detected. Continue monitoring.")
        
        return recommendations
    
    def _determine_risk_level(self, score: float, threats: List[ThreatIndicator]) -> str:
        """Determine overall risk level"""
        critical_threats = len([t for t in threats if t.severity == 'critical'])
        high_threats = len([t for t in threats if t.severity == 'high'])
        
        if score < 30 or critical_threats >= 3:
            return 'critical'
        elif score < 50 or critical_threats >= 1 or high_threats >= 3:
            return 'high' 
        elif score < 70 or high_threats >= 1:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_confidence_interval(self, df: pd.DataFrame, score: float) -> Tuple[float, float]:
        """Calculate confidence interval for security score"""
        n_samples = len(df)
        if n_samples < 30:
            return (max(0, score - 20), min(100, score + 20))
        
        failure_rate = 1 - df['access_granted'].mean()
        std_error = np.sqrt(failure_rate * (1 - failure_rate) / n_samples)
        
        margin_of_error = 1.96 * std_error * 100
        
        lower_bound = max(0, score - margin_of_error)
        upper_bound = min(100, score + margin_of_error)
        
        return (round(lower_bound, 2), round(upper_bound, 2))
    
    def _convert_to_legacy_format(self, result: SecurityAssessment) -> Dict[str, Any]:
        """Convert SecurityAssessment to legacy dictionary format"""
        return {
            'security_score': result.overall_score,
            'risk_level': result.risk_level,
            'confidence_interval': result.confidence_interval,
            'threat_count': len(result.threat_indicators),
            'critical_threats': len([t for t in result.threat_indicators if t.severity == 'critical']),
            'recommendations': result.recommendations,
            'pattern_analysis': result.pattern_analysis,
            'threats': [
                {
                    'type': t.threat_type,
                    'severity': t.severity,
                    'confidence': t.confidence,
                    'description': t.description,
                    'affected_entities': t.affected_entities
                } for t in result.threat_indicators
            ],
            # Legacy compatibility fields
            'failed_attempts': len([t for t in result.threat_indicators if 'failure' in t.threat_type]),
            'score': result.overall_score
        }
    
    def _empty_security_assessment(self) -> SecurityAssessment:
        """Return empty security assessment for error cases"""
        return SecurityAssessment(
            overall_score=0.0,
            risk_level='unknown',
            confidence_interval=(0.0, 0.0),
            threat_indicators=[],
            pattern_analysis={},
            recommendations=['Unable to perform security analysis due to data issues']
        )
    
    def _empty_legacy_result(self) -> Dict[str, Any]:
        """Return empty result in legacy format"""
        return {
            'security_score': 0.0,
            'risk_level': 'unknown',
            'confidence_interval': (0.0, 0.0),
            'threat_count': 0,
            'critical_threats': 0,
            'recommendations': ['Unable to perform security analysis due to data issues'],
            'pattern_analysis': {},
            'threats': [],
            'failed_attempts': 0,
            'score': 0.0
        }

# Factory function for compatibility
def create_security_analyzer(**kwargs) -> SecurityPatternsAnalyzer:
    """Factory function to create security analyzer"""
    return SecurityPatternsAnalyzer(**kwargs)

# Alias for enhanced version
EnhancedSecurityAnalyzer = SecurityPatternsAnalyzer
create_enhanced_security_analyzer = create_security_analyzer

# Export for compatibility
__all__ = ['SecurityPatternsAnalyzer', 'create_security_analyzer', 'EnhancedSecurityAnalyzer']