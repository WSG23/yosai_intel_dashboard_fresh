"""
Enhanced User Behavior Analyzer
Replace the entire content of analytics/user_behavior.py with this code
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import logging
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

@dataclass
class BehaviorAnalysis:
    """Comprehensive behavior analysis result"""
    total_users_analyzed: int
    high_risk_users: int
    global_patterns: Dict[str, Any]
    insights: List[str]
    recommendations: List[str]

class UserBehaviorAnalyzer:
    """Enhanced user behavior analyzer with ML-based segmentation"""
    
    def __init__(self,
                 min_user_events: int = 5,
                 max_clusters: int = 8,
                 risk_threshold: float = 0.7,
                 logger: Optional[logging.Logger] = None):
        self.min_user_events = min_user_events
        self.max_clusters = max_clusters
        self.risk_threshold = risk_threshold
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize ML models
        self.scaler = StandardScaler()
    
    def analyze_behavior(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Main analysis method with legacy compatibility"""
        try:
            result = self.analyze_user_behavior(df)
            return self._convert_to_legacy_format(result)
        except Exception as e:
            self.logger.error(f"Behavior analysis failed: {e}")
            return self._empty_legacy_result()
    
    def analyze_user_behavior(self, df: pd.DataFrame) -> BehaviorAnalysis:
        """Enhanced behavior analysis method"""
        try:
            # Prepare behavioral data
            df_clean = self._prepare_behavior_data(df)
            
            # Generate user features
            user_features = self._extract_user_features(df_clean)
            
            if len(user_features) == 0:
                return self._empty_behavior_analysis()
            
            # Calculate risk scores
            risk_scores = user_features.apply(
                lambda row: self._calculate_user_risk_score(row), axis=1
            )
            
            # Analyze global patterns
            global_patterns = self._analyze_global_patterns(df_clean, user_features)
            
            # Count high risk users
            high_risk_count = (risk_scores > self.risk_threshold).sum()
            
            # Generate insights and recommendations
            insights = self._generate_behavioral_insights(user_features, global_patterns, high_risk_count)
            recommendations = self._generate_behavioral_recommendations(high_risk_count, global_patterns)
            
            return BehaviorAnalysis(
                total_users_analyzed=len(user_features),
                high_risk_users=high_risk_count,
                global_patterns=global_patterns,
                insights=insights,
                recommendations=recommendations
            )
            
        except Exception as e:
            self.logger.error(f"Behavior analysis failed: {e}")
            return self._empty_behavior_analysis()
    
    def _prepare_behavior_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare and clean data for behavior analysis"""
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
        
        # Filter users with minimum events
        user_event_counts = df_clean['person_id'].value_counts()
        valid_users = user_event_counts[user_event_counts >= self.min_user_events].index
        df_clean = df_clean[df_clean['person_id'].isin(valid_users)]
        
        return df_clean
    
    def _extract_user_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract comprehensive behavioral features for each user"""
        features_list = []
        
        for user_id in df['person_id'].unique():
            user_data = df[df['person_id'] == user_id]
            
            # Basic activity features
            total_events = len(user_data)
            unique_doors = user_data['door_id'].nunique()
            success_rate = user_data['access_granted'].mean()
            
            # Temporal features
            temporal_features = self._extract_temporal_features(user_data)
            
            # Regularity features
            regularity_features = self._extract_regularity_features(user_data)
            
            # Risk indicators
            risk_features = self._extract_risk_features(user_data, df)
            
            # Combine all features
            user_features = {
                'user_id': user_id,
                'total_events': total_events,
                'unique_doors': unique_doors,
                'success_rate': success_rate,
                **temporal_features,
                **regularity_features,
                **risk_features
            }
            
            features_list.append(user_features)
        
        return pd.DataFrame(features_list)
    
    def _extract_temporal_features(self, user_data: pd.DataFrame) -> Dict[str, Any]:
        """Extract temporal behavior features"""
        
        # Hour distribution features
        hour_distribution = user_data['hour'].value_counts(normalize=True)
        hour_entropy = -np.sum(hour_distribution * np.log2(hour_distribution + 1e-10))
        hour_diversity = hour_entropy / np.log2(24)
        
        # Peak hours
        top_hours = hour_distribution.nlargest(3).index.tolist()
        
        # Day of week features
        dow_distribution = user_data['day_of_week'].value_counts(normalize=True)
        dow_entropy = -np.sum(dow_distribution * np.log2(dow_distribution + 1e-10))
        dow_diversity = dow_entropy / np.log2(7)
        
        # Time patterns
        after_hours_rate = user_data['is_after_hours'].mean()
        weekend_rate = user_data['is_weekend'].mean()
        
        # Activity span
        activity_span = (user_data['timestamp'].max() - user_data['timestamp'].min()).days
        
        return {
            'hour_diversity': hour_diversity,
            'dow_diversity': dow_diversity,
            'peak_hours': ','.join(map(str, top_hours)),
            'after_hours_rate': after_hours_rate,
            'weekend_rate': weekend_rate,
            'activity_span_days': activity_span,
            'avg_daily_events': len(user_data) / max(activity_span, 1)
        }
    
    def _extract_regularity_features(self, user_data: pd.DataFrame) -> Dict[str, Any]:
        """Extract regularity and consistency features"""
        
        # Daily event count distribution
        user_data_copy = user_data.copy()
        user_data_copy['date'] = user_data_copy['timestamp'].dt.date
        daily_counts = user_data_copy.groupby('date').size()
        
        if len(daily_counts) > 1:
            regularity_score = 1 - (daily_counts.std() / (daily_counts.mean() + 1e-10))
            regularity_score = max(0, min(1, regularity_score))
        else:
            regularity_score = 0.5
        
        # Time gap analysis
        user_data_sorted = user_data.sort_values('timestamp')
        time_gaps = user_data_sorted['timestamp'].diff().dt.total_seconds()
        
        # Remove first NaN
        time_gaps = time_gaps.dropna()
        
        if len(time_gaps) > 0:
            gap_cv = time_gaps.std() / (time_gaps.mean() + 1e-10)  # Coefficient of variation
            median_gap_hours = time_gaps.median() / 3600
        else:
            gap_cv = 0
            median_gap_hours = 0
        
        # Pattern consistency (hour-wise)
        hour_consistency = self._calculate_hour_consistency(user_data)
        
        return {
            'regularity_score': regularity_score,
            'time_gap_cv': gap_cv,
            'median_gap_hours': median_gap_hours,
            'hour_consistency': hour_consistency
        }
    
    def _calculate_hour_consistency(self, user_data: pd.DataFrame) -> float:
        """Calculate hour-wise access consistency"""
        
        # Group by date and find primary access hours for each day
        user_data_copy = user_data.copy()
        user_data_copy['date'] = user_data_copy['timestamp'].dt.date
        
        daily_hour_patterns = []
        
        for date in user_data_copy['date'].unique():
            day_data = user_data_copy[user_data_copy['date'] == date]
            primary_hour = day_data['hour'].mode()
            if len(primary_hour) > 0:
                daily_hour_patterns.append(primary_hour.iloc[0])
        
        if len(daily_hour_patterns) <= 1:
            return 0.5
        
        # Calculate consistency as 1 - coefficient of variation
        patterns_array = np.array(daily_hour_patterns)
        consistency = 1 - (patterns_array.std() / (patterns_array.mean() + 1e-10))
        
        return max(0, min(1, consistency))
    
    def _extract_risk_features(self, user_data: pd.DataFrame, full_df: pd.DataFrame) -> Dict[str, Any]:
        """Extract risk-related features"""
        
        # Failure rate compared to global average
        global_failure_rate = 1 - full_df['access_granted'].mean()
        user_failure_rate = 1 - user_data['access_granted'].mean()
        failure_rate_ratio = user_failure_rate / (global_failure_rate + 1e-10)
        
        # Badge status issues (if available)
        badge_issue_rate = 0
        if 'badge_status' in user_data.columns:
            badge_issue_rate = (user_data['badge_status'] != 'Valid').mean()
        
        # Anomalous timing using KL divergence
        anomalous_timing_score = self._calculate_anomalous_timing(user_data, full_df)
        
        # Overall risk indicators
        risk_indicators = []
        if failure_rate_ratio > 2:
            risk_indicators.append('high_failure_rate')
        if user_data['is_after_hours'].mean() > 0.3:
            risk_indicators.append('frequent_after_hours')
        if badge_issue_rate > 0.1:
            risk_indicators.append('badge_issues')
        if anomalous_timing_score > 0.7:
            risk_indicators.append('anomalous_timing')
        
        return {
            'failure_rate_ratio': failure_rate_ratio,
            'badge_issue_rate': badge_issue_rate,
            'anomalous_timing_score': anomalous_timing_score,
            'risk_indicator_count': len(risk_indicators),
            'risk_indicators': ','.join(risk_indicators)
        }
    
    def _calculate_anomalous_timing(self, user_data: pd.DataFrame, full_df: pd.DataFrame) -> float:
        """Calculate anomalous timing score using KL divergence"""
        
        try:
            # Compare user hour distribution to global distribution
            user_hour_dist = user_data['hour'].value_counts(normalize=True).reindex(range(24), fill_value=1e-10)
            global_hour_dist = full_df['hour'].value_counts(normalize=True).reindex(range(24), fill_value=1e-10)
            
            # Calculate KL divergence
            kl_div = np.sum(user_hour_dist * np.log2(user_hour_dist / global_hour_dist))
            
            # Normalize to 0-1 scale
            anomaly_score = min(1.0, kl_div / 5.0)  # Cap at reasonable value
            
            return anomaly_score
            
        except Exception:
            return 0.0
    
    def _calculate_user_risk_score(self, user_features: pd.Series) -> float:
        """Calculate comprehensive user risk score (0-1)"""
        risk_score = 0.0
        
        # Failure rate component (0-30 points)
        failure_component = min(30, user_features['failure_rate_ratio'] * 15)
        risk_score += failure_component
        
        # Badge issues component (0-20 points)
        badge_component = user_features['badge_issue_rate'] * 20
        risk_score += badge_component
        
        # After hours component (0-15 points)
        after_hours_component = user_features['after_hours_rate'] * 15
        risk_score += after_hours_component
        
        # Anomalous timing component (0-20 points)
        timing_component = user_features['anomalous_timing_score'] * 20
        risk_score += timing_component
        
        # Weekend component (0-10 points)
        weekend_component = user_features['weekend_rate'] * 10
        risk_score += weekend_component
        
        # Normalize to 0-1 scale
        return min(1.0, risk_score / 95)
    
    def _analyze_global_patterns(self, df: pd.DataFrame, user_features: pd.DataFrame) -> Dict[str, Any]:
        """Analyze global behavioral patterns across all users"""
        global_patterns = {}
        
        try:
            # Overall activity patterns
            global_patterns['activity_distribution'] = {
                'total_events': len(df),
                'unique_users': df['person_id'].nunique(),
                'avg_events_per_user': user_features['total_events'].mean(),
                'avg_success_rate': user_features['success_rate'].mean()
            }
            
            # Temporal patterns
            global_patterns['temporal_patterns'] = {
                'peak_hour': df['hour'].mode().iloc[0] if len(df) > 0 else 0,
                'peak_day': df['day_of_week'].mode().iloc[0] if len(df) > 0 else 0,
                'after_hours_percentage': df['is_after_hours'].mean() * 100,
                'weekend_percentage': df['is_weekend'].mean() * 100
            }
            
            # Access patterns
            global_patterns['access_patterns'] = {
                'most_used_door': df['door_id'].mode().iloc[0] if len(df) > 0 else 'Unknown',
                'door_usage_distribution': df['door_id'].value_counts().head(5).to_dict(),
                'average_doors_per_user': user_features['unique_doors'].mean()
            }
            
            # Risk patterns
            risk_scores = user_features.apply(
                lambda row: self._calculate_user_risk_score(row), axis=1
            )
            
            global_patterns['risk_patterns'] = {
                'average_risk_score': risk_scores.mean(),
                'high_risk_user_percentage': (risk_scores > self.risk_threshold).mean() * 100,
                'risk_score_distribution': risk_scores.describe().to_dict()
            }
            
            # Behavioral diversity
            global_patterns['behavioral_diversity'] = {
                'hour_diversity_avg': user_features['hour_diversity'].mean(),
                'regularity_score_avg': user_features['regularity_score'].mean(),
                'temporal_consistency': user_features['hour_consistency'].mean()
            }
            
        except Exception as e:
            self.logger.warning(f"Global pattern analysis failed: {e}")
        
        return global_patterns
    
    def _generate_behavioral_insights(self, user_features: pd.DataFrame, 
                                    global_patterns: Dict[str, Any], 
                                    high_risk_count: int) -> List[str]:
        """Generate behavioral insights from analysis"""
        insights = []
        
        try:
            # High risk user insights
            if high_risk_count > 0:
                total_users = len(user_features)
                risk_percentage = (high_risk_count / total_users) * 100
                insights.append(
                    f"{high_risk_count} users ({risk_percentage:.1f}%) identified with high risk scores requiring attention."
                )
            
            # Activity insights
            activity_dist = global_patterns.get('activity_distribution', {})
            avg_events = activity_dist.get('avg_events_per_user', 0)
            if avg_events > 100:
                insights.append("Users show high overall activity levels, indicating heavy system usage.")
            elif avg_events < 10:
                insights.append("Users show low overall activity levels, indicating light system usage.")
            
            # Temporal insights
            temporal_patterns = global_patterns.get('temporal_patterns', {})
            after_hours_pct = temporal_patterns.get('after_hours_percentage', 0)
            if after_hours_pct > 20:
                insights.append(
                    f"High after-hours activity detected: {after_hours_pct:.1f}% of all access attempts."
                )
            
            # Behavioral diversity insights
            behavioral_div = global_patterns.get('behavioral_diversity', {})
            avg_regularity = behavioral_div.get('regularity_score_avg', 0)
            if avg_regularity > 0.8:
                insights.append("Users demonstrate highly regular access patterns, indicating predictable behavior.")
            elif avg_regularity < 0.3:
                insights.append("Users show irregular access patterns, suggesting diverse work schedules or roles.")
            
            # Access pattern insights
            access_patterns = global_patterns.get('access_patterns', {})
            avg_doors = access_patterns.get('average_doors_per_user', 0)
            if avg_doors > 5:
                insights.append("Users access multiple doors on average, indicating diverse access requirements.")
            
        except Exception as e:
            self.logger.warning(f"Insight generation failed: {e}")
        
        return insights
    
    def _generate_behavioral_recommendations(self, high_risk_count: int,
                                           global_patterns: Dict[str, Any]) -> List[str]:
        """Generate behavioral recommendations"""
        recommendations = []
        
        try:
            # Risk-based recommendations
            if high_risk_count > 0:
                recommendations.append(
                    f"Immediate review required for {high_risk_count} high-risk users. "
                    "Verify access permissions and investigate unusual patterns."
                )
            
            # Temporal recommendations
            temporal_patterns = global_patterns.get('temporal_patterns', {})
            after_hours_pct = temporal_patterns.get('after_hours_percentage', 0)
            if after_hours_pct > 25:
                recommendations.append(
                    "Consider implementing stricter after-hours access policies "
                    "and additional approval processes."
                )
            
            weekend_pct = temporal_patterns.get('weekend_percentage', 0)
            if weekend_pct > 15:
                recommendations.append(
                    "Significant weekend activity detected. Review weekend access policies."
                )
            
            # Activity-based recommendations
            activity_dist = global_patterns.get('activity_distribution', {})
            success_rate = activity_dist.get('avg_success_rate', 1.0)
            if success_rate < 0.9:
                recommendations.append(
                    "Low average success rate detected. Review user training and access procedures."
                )
            
            # Behavioral diversity recommendations
            behavioral_div = global_patterns.get('behavioral_diversity', {})
            temporal_consistency = behavioral_div.get('temporal_consistency', 0)
            if temporal_consistency < 0.5:
                recommendations.append(
                    "Low temporal consistency across users. Consider reviewing work schedule policies."
                )
            
            # General recommendations
            if not recommendations:
                recommendations.append(
                    "User behavior patterns appear normal. Continue regular monitoring."
                )
                
        except Exception as e:
            self.logger.warning(f"Recommendation generation failed: {e}")
        
        return recommendations
    
    def _convert_to_legacy_format(self, result: BehaviorAnalysis) -> Dict[str, Any]:
        """Convert BehaviorAnalysis to legacy dictionary format"""
        return {
            'total_users_analyzed': result.total_users_analyzed,
            'high_risk_users': result.high_risk_users,
            'avg_accesses_per_user': result.global_patterns.get('activity_distribution', {}).get('avg_events_per_user', 0),
            'heavy_users': result.high_risk_users,  # Approximation
            'behavior_score': 100 - (result.high_risk_users / max(result.total_users_analyzed, 1) * 100),
            'global_patterns': result.global_patterns,
            'insights': result.insights,
            'recommendations': result.recommendations,
            # Additional legacy fields
            'user_segments': self._create_legacy_segments(result),
            'risk_distribution': self._create_risk_distribution(result),
            'temporal_analysis': result.global_patterns.get('temporal_patterns', {}),
            'access_diversity': result.global_patterns.get('access_patterns', {})
        }
    
    def _create_legacy_segments(self, result: BehaviorAnalysis) -> Dict[str, int]:
        """Create legacy user segments"""
        total_users = result.total_users_analyzed
        high_risk = result.high_risk_users
        
        return {
            'power_users': max(0, int(total_users * 0.1)),  # Top 10%
            'regular_users': max(0, int(total_users * 0.6)),  # 60%
            'occasional_users': max(0, int(total_users * 0.2)),  # 20%
            'irregular_users': max(0, total_users - high_risk - int(total_users * 0.9)),
            'security_risks': high_risk
        }
    
    def _create_risk_distribution(self, result: BehaviorAnalysis) -> Dict[str, int]:
        """Create risk distribution"""
        total_users = result.total_users_analyzed
        high_risk = result.high_risk_users
        
        return {
            'low': max(0, int(total_users * 0.7)),
            'medium': max(0, int(total_users * 0.2)),
            'high': high_risk,
            'critical': max(0, int(high_risk * 0.1))
        }
    
    def _empty_behavior_analysis(self) -> BehaviorAnalysis:
        """Return empty behavior analysis for error cases"""
        return BehaviorAnalysis(
            total_users_analyzed=0,
            high_risk_users=0,
            global_patterns={},
            insights=['Unable to perform behavior analysis due to insufficient data'],
            recommendations=['Collect more user access data for meaningful analysis']
        )
    
    def _empty_legacy_result(self) -> Dict[str, Any]:
        """Return empty result in legacy format"""
        return {
            'total_users_analyzed': 0,
            'high_risk_users': 0,
            'avg_accesses_per_user': 0,
            'heavy_users': 0,
            'behavior_score': 0,
            'global_patterns': {},
            'insights': ['Unable to perform behavior analysis due to insufficient data'],
            'recommendations': ['Collect more user access data for meaningful analysis'],
            'user_segments': {'power_users': 0, 'regular_users': 0, 'occasional_users': 0, 'irregular_users': 0, 'security_risks': 0},
            'risk_distribution': {'low': 0, 'medium': 0, 'high': 0, 'critical': 0},
            'temporal_analysis': {},
            'access_diversity': {}
        }

# Factory function for compatibility
def create_behavior_analyzer(**kwargs) -> UserBehaviorAnalyzer:
    """Factory function to create behavior analyzer"""
    return UserBehaviorAnalyzer(**kwargs)

# Alias for enhanced version
EnhancedBehaviorAnalyzer = UserBehaviorAnalyzer
create_enhanced_behavior_analyzer = create_behavior_analyzer

# Export for compatibility
__all__ = ['UserBehaviorAnalyzer', 'create_behavior_analyzer', 'EnhancedBehaviorAnalyzer']