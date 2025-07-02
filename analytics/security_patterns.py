"""
Security Patterns Analytics Module
Analyzes security-related patterns in access control data
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from .security_metrics import SecurityMetrics
from .security_score_calculator import SecurityScoreCalculator
from dataclasses import dataclass
import logging

@dataclass
class SecurityPattern:
    """Security pattern data structure"""
    pattern_type: str
    severity: str
    count: int
    affected_entities: List[str]
    risk_score: float
    description: str
    recommendation: str

class SecurityPatternsAnalyzer:
    """Advanced security patterns analysis"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.score_calculator = SecurityScoreCalculator()

    def analyze_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Main analysis function for security patterns"""
        try:
            if df.empty:
                return self._empty_result()
            
            df = self._prepare_data(df)
            
            patterns = {
                'failed_access_patterns': self._analyze_failed_access(df),
                'unauthorized_attempts': self._analyze_unauthorized_attempts(df),
                'suspicious_timing': self._analyze_suspicious_timing(df),
                'badge_anomalies': self._analyze_badge_anomalies(df),
                'device_security_issues': self._analyze_device_issues(df),
                'access_violations': self._analyze_access_violations(df),
                'security_score': self._calculate_security_score(df),
                'threat_summary': self._generate_threat_summary(df)
            }
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Security patterns analysis failed: {e}")
            return self._empty_result()
    
    def _prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare and validate data for analysis"""
        df = df.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        # Validate and add missing temporal columns
        if 'is_after_hours' not in df.columns:
            hour = df['timestamp'].dt.hour
            df['is_after_hours'] = (hour < 8) | (hour >= 18)

        if 'is_weekend' not in df.columns:
            df['is_weekend'] = df['timestamp'].dt.weekday >= 5
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.day_name()
        return df
    
    def _analyze_failed_access(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze failed access attempts patterns"""
        failed_attempts = df[df['access_result'] == 'Denied']
        
        if failed_attempts.empty:
            return {'total': 0, 'patterns': [], 'risk_level': 'low'}
        
        # Group by person and analyze repeated failures
        failure_by_person = failed_attempts.groupby('person_id').agg({
            'event_id': 'count',
            'door_id': 'nunique',
            'timestamp': ['min', 'max']
        })
        # Flatten the MultiIndex columns
        failure_by_person.columns = ['event_count', 'unique_doors', 'first_ts', 'last_ts']
        
        # Identify high-risk patterns
        high_failure_users = failure_by_person[
            failure_by_person['event_count'] >= 5
        ].index.tolist()
        
        # Analyze failure timing patterns
        failure_timing = failed_attempts.groupby(['hour', 'day_of_week']).size()
        peak_failure_times = failure_timing.nlargest(5)
        
        # Door-specific failure analysis
        door_failures = failed_attempts.groupby('door_id').agg({
            'event_id': 'count',
            'person_id': 'nunique'
        }).sort_values('event_id', ascending=False)
        
        return {
            'total': len(failed_attempts),
            'failure_rate': len(failed_attempts) / len(df) * 100,
            'high_risk_users': high_failure_users,
            'peak_failure_times': peak_failure_times.to_dict(),
            'top_failure_doors': door_failures.head(10).to_dict(),
            'patterns': self._extract_failure_patterns(failed_attempts),
            'risk_level': self._assess_failure_risk(len(failed_attempts), len(df))
        }
    
    def _analyze_unauthorized_attempts(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze unauthorized access attempts"""
        # Multiple criteria for unauthorized attempts
        unauthorized = df[
            (df['access_result'] == 'Denied') |
            (df['badge_status'] == 'Invalid') |
            (df['entry_without_badge'] == True)
        ]
        
        if unauthorized.empty:
            return {'total': 0, 'severity': 'low', 'locations': []}
        
        # Analyze by location and time
        location_analysis = unauthorized.groupby('door_id').agg({
            'event_id': 'count',
            'person_id': 'nunique',
            'timestamp': lambda x: x.dt.hour.mode().iloc[0] if len(x) > 0 else 0
        })
        
        # Time-based analysis
        after_hours_unauthorized = unauthorized[unauthorized['is_after_hours']]
        weekend_unauthorized = unauthorized[unauthorized['is_weekend']]
        
        return {
            'total': len(unauthorized),
            'after_hours_count': len(after_hours_unauthorized),
            'weekend_count': len(weekend_unauthorized),
            'affected_doors': location_analysis.to_dict(),
            'severity': self._assess_unauthorized_severity(unauthorized),
            'repeat_offenders': self._identify_repeat_offenders(unauthorized)
        }
    
    def _analyze_suspicious_timing(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze suspicious timing patterns"""
        # Define suspicious times (very early/late hours)
        very_early = df[(df['hour'] >= 0) & (df['hour'] <= 4)]
        very_late = df[(df['hour'] >= 23) | (df['hour'] <= 1)]
        
        # Weekend access analysis
        weekend_access = df[df['is_weekend']]
        
        # Rapid sequential access (potential tailgating)
        df_sorted = df.sort_values(['person_id', 'timestamp'])
        df_sorted['time_diff'] = df_sorted.groupby('person_id')['timestamp'].diff()
        rapid_access = df_sorted[df_sorted['time_diff'] < pd.Timedelta(minutes=2)]
        
        return {
            'after_hours_events': len(df[df['is_after_hours']]),
            'weekend_events': len(weekend_access),
            'very_early_access': len(very_early),
            'very_late_access': len(very_late),
            'rapid_sequential_access': len(rapid_access),
            'suspicious_patterns': self._identify_timing_patterns(df)
        }
    
    def _analyze_badge_anomalies(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze badge-related security anomalies"""
        badge_issues = df[df['badge_status'] != 'Valid']
        
        if badge_issues.empty:
            return {'total': 0, 'issues': {}, 'affected_users': []}
        
        # Group by badge status
        status_breakdown = badge_issues['badge_status'].value_counts().to_dict()
        
        # Users with frequent badge issues
        problematic_users = badge_issues.groupby('person_id').size()
        frequent_issues = problematic_users[problematic_users >= 3].to_dict()
        
        # Badge issues by door
        door_badge_issues = badge_issues.groupby('door_id').agg({
            'event_id': 'count',
            'badge_status': lambda x: x.mode().iloc[0] if len(x) > 0 else 'Unknown'
        })
        
        return {
            'total': len(badge_issues),
            'issue_rate': len(badge_issues) / len(df) * 100,
            'status_breakdown': status_breakdown,
            'frequent_issue_users': frequent_issues,
            'door_issues': door_badge_issues.to_dict(),
            'severity': self._assess_badge_severity(badge_issues, df)
        }
    
    def _analyze_device_issues(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze device status security issues"""
        if 'device_status' not in df.columns:
            return {'total': 0, 'issues': {}}
        
        device_issues = df[df['device_status'] != 'normal']
        
        if device_issues.empty:
            return {'total': 0, 'issues': {}, 'affected_doors': []}
        
        # Group by device status
        status_types = device_issues['device_status'].value_counts().to_dict()
        
        # Doors with device issues
        door_device_issues = device_issues.groupby('door_id').agg({
            'event_id': 'count',
            'device_status': lambda x: list(x.unique())
        })
        
        return {
            'total': len(device_issues),
            'status_types': status_types,
            'affected_doors': door_device_issues.to_dict(),
            'issue_rate': len(device_issues) / len(df) * 100
        }
    
    def _analyze_access_violations(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze access policy violations"""
        # Define violations based on multiple criteria
        violations = df[
            (df['access_result'] == 'Denied') |
            (df['entry_without_badge'] == True) |
            ((df['door_held_open_time'] > 30) & (df['door_held_open_time'] < 9999))
        ]
        
        if violations.empty:
            return {'total': 0, 'violation_types': {}}
        
        violation_types = {
            'access_denied': len(df[df['access_result'] == 'Denied']),
            'no_badge_entry': len(df[df['entry_without_badge'] == True]),
            'door_held_too_long': len(df[df['door_held_open_time'] > 30])
        }
        
        # Critical area violations
        critical_doors = ['DOOR002', 'DOOR003', 'DOOR005']  # Based on schema
        critical_violations = violations[violations['door_id'].isin(critical_doors)]
        
        return {
            'total': len(violations),
            'violation_types': violation_types,
            'critical_area_violations': len(critical_violations),
            'violation_rate': len(violations) / len(df) * 100,
            'severity': 'high' if len(critical_violations) > 0 else 'medium'
        }
    
    def _calculate_security_score(self, df: pd.DataFrame) -> SecurityMetrics:

        """Calculate overall security score using external calculator."""
        result = self.score_calculator.calculate_security_score_fixed(df)
        return SecurityMetrics(
            score=result.get("score", 0.0),
            threat_level=result.get("threat_level", "low"),
            confidence_interval=result.get("confidence_interval", (0.0, 0.0)),
            method=result.get("method", "none"),

        )
    
    def _generate_threat_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate comprehensive threat summary"""
        threats = []
        
        # High failure rate threat
        failure_rate = len(df[df['access_result'] == 'Denied']) / len(df) * 100
        if failure_rate > 15:
            threats.append({
                'type': 'high_failure_rate',
                'severity': 'high' if failure_rate > 25 else 'medium',
                'description': f'High access failure rate: {failure_rate:.1f}%'
            })
        
        # After-hours access threat
        after_hours_count = len(df[df['is_after_hours']])
        if after_hours_count > len(df) * 0.1:
            threats.append({
                'type': 'excessive_after_hours',
                'severity': 'medium',
                'description': f'High after-hours access: {after_hours_count} events'
            })
        
        # Badge security threat
        invalid_badge_rate = len(df[df['badge_status'] != 'Valid']) / len(df) * 100
        if invalid_badge_rate > 5:
            threats.append({
                'type': 'badge_security',
                'severity': 'high' if invalid_badge_rate > 15 else 'medium',
                'description': f'High invalid badge rate: {invalid_badge_rate:.1f}%'
            })
        
        return {
            'threat_count': len(threats),
            'threats': threats,
            'overall_risk': self._assess_overall_risk(threats)
        }
    
    # Helper methods
    def _extract_failure_patterns(self, failed_attempts: pd.DataFrame) -> List[Dict]:
        """Extract specific failure patterns"""
        # Repeated failures by same user
        repeat_users = (
            failed_attempts.groupby('person_id')
            .size()
            .loc[lambda s: s >= 3]
            .reset_index(name='count')
        )

        if repeat_users.empty:
            return []

        repeat_users['type'] = 'repeated_failures'
        repeat_users['severity'] = repeat_users['count'].apply(
            lambda c: 'high' if c >= 5 else 'medium'
        )

        return repeat_users.rename(columns={'person_id': 'user'})[
            ['type', 'user', 'count', 'severity']
        ].to_dict('records')
    
    def _assess_failure_risk(self, failures: int, total: int) -> str:
        """Assess risk level based on failure rate"""
        rate = failures / total * 100
        if rate > 20:
            return 'high'
        elif rate > 10:
            return 'medium'
        else:
            return 'low'
    
    def _assess_unauthorized_severity(self, unauthorized: pd.DataFrame) -> str:
        """Assess severity of unauthorized attempts"""
        if len(unauthorized) > 20:
            return 'high'
        elif len(unauthorized) > 5:
            return 'medium'
        else:
            return 'low'
    
    def _identify_repeat_offenders(self, unauthorized: pd.DataFrame) -> List[str]:
        """Identify users with multiple unauthorized attempts"""
        offenders = unauthorized.groupby('person_id').size()
        return offenders[offenders >= 3].index.tolist()
    
    def _identify_timing_patterns(self, df: pd.DataFrame) -> List[Dict]:
        """Identify suspicious timing patterns"""
        # Users accessing at unusual times
        frequent_after_hours = (
            df[df['is_after_hours']]
            .groupby('person_id')
            .size()
            .loc[lambda s: s >= 5]
            .reset_index(name='count')
        )

        if frequent_after_hours.empty:
            return []

        frequent_after_hours['type'] = 'frequent_after_hours'

        return frequent_after_hours.rename(columns={'person_id': 'user'})[
            ['type', 'user', 'count']
        ].to_dict('records')
    
    def _assess_badge_severity(self, badge_issues: pd.DataFrame, df: pd.DataFrame) -> str:
        """Assess severity of badge issues"""
        rate = len(badge_issues) / len(df) * 100
        if rate > 15:
            return 'high'
        elif rate > 5:
            return 'medium'
        else:
            return 'low'
    
    def _assess_overall_risk(self, threats: List[Dict]) -> str:
        """Assess overall security risk"""
        if not threats:
            return 'low'
        
        high_severity_count = sum(1 for t in threats if t['severity'] == 'high')
        
        if high_severity_count >= 2:
            return 'critical'
        elif high_severity_count >= 1:
            return 'high'
        else:
            return 'medium'
    
    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result structure"""
        return {
            'failed_access_patterns': {'total': 0, 'patterns': []},
            'unauthorized_attempts': {'total': 0, 'severity': 'low'},
            'suspicious_timing': {'after_hours_events': 0},
            'badge_anomalies': {'total': 0, 'issues': {}},
            'device_security_issues': {'total': 0, 'issues': {}},
            'access_violations': {'total': 0, 'violation_types': {}},
            'security_score': SecurityMetrics(
                score=0,
                threat_level='low',
                confidence_interval=(0.0, 0.0),
                method='none',
            ),
            'threat_summary': {'threat_count': 0, 'threats': []}
        }

# Factory function
def create_security_analyzer() -> SecurityPatternsAnalyzer:
    """Create security patterns analyzer instance"""
    return SecurityPatternsAnalyzer()

# Export
__all__ = ['SecurityPatternsAnalyzer', 'SecurityPattern', 'create_security_analyzer', 'SecurityMetrics']
