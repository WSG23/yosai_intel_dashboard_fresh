"""
User Behavior Analytics Module
Analyzes user behavior patterns and characteristics in access control data
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
import logging
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from scipy import stats

from file_conversion.unicode_handler import UnicodeCleaner

@dataclass
class UserProfile:
    """User behavior profile data structure"""
    user_id: str
    behavior_type: str  # 'regular', 'irregular', 'power_user', 'occasional'
    activity_score: float
    risk_score: float
    patterns: Dict[str, Any]
    anomalies: List[Dict[str, Any]]

class UserBehaviorAnalyzer:
    """Advanced user behavior analysis"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def analyze_behavior(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Main analysis function for user behavior"""
        try:
            if df.empty:
                return self._empty_result()
            
            df = self._prepare_data(df)
            
            behavior = {
                'user_profiles': self._create_user_profiles(df),
                'behavior_clustering': self._perform_behavior_clustering(df),
                'access_patterns': self._analyze_access_patterns(df),
                'temporal_behavior': self._analyze_temporal_behavior(df),
                'location_preferences': self._analyze_location_preferences(df),
                'behavioral_anomalies': self._detect_behavioral_anomalies(df),
                'user_segments': self._segment_users(df),
                'behavior_summary': self._generate_behavior_summary(df)
            }
            
            return behavior
            
        except Exception as e:
            self.logger.error(f"User behavior analysis failed: {e}")
            return self._empty_result()
    
    def _prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare and validate data for behavior analysis.

        Text columns are sanitized using ``UnicodeCleaner.clean_dataframe`` to
        remove invalid Unicode surrogates before temporal fields are derived.
        """
        df = UnicodeCleaner.clean_dataframe(df)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.day_name()
        df['is_weekend'] = df['timestamp'].dt.weekday >= 5
        df['is_business_hours'] = (df['hour'] >= 8) & (df['hour'] <= 18)
        df['month'] = df['timestamp'].dt.month
        df['week'] = df['timestamp'].dt.isocalendar().week
        return df
    
    def _create_user_profiles(self, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """Create comprehensive user behavior profiles"""
        user_profiles = {}
        
        for user_id in df['person_id'].unique():
            user_data = df[df['person_id'] == user_id]
            profile = self._build_individual_profile(user_id, user_data, df)
            user_profiles[user_id] = profile
        
        return user_profiles
    
    def _build_individual_profile(self, user_id: str, user_data: pd.DataFrame, 
                                  full_df: pd.DataFrame) -> Dict[str, Any]:
        """Build detailed profile for individual user"""
        
        # Basic statistics
        total_events = len(user_data)
        unique_doors = user_data['door_id'].nunique()
        success_rate = (user_data['access_result'] == 'Granted').mean() * 100
        
        # Time span analysis
        first_access = user_data['timestamp'].min()
        last_access = user_data['timestamp'].max()
        activity_span = (last_access - first_access).days
        
        # Behavioral characteristics
        preferred_hours = user_data['hour'].mode().tolist()
        preferred_days = user_data['day_of_week'].mode().tolist()
        after_hours_events = len(user_data[~user_data['is_business_hours']])
        weekend_events = len(user_data[user_data['is_weekend']])
        
        # Activity patterns
        daily_activity = user_data.groupby('date')['event_id'].count()
        activity_consistency = 1 - (daily_activity.std() / daily_activity.mean()) if daily_activity.mean() > 0 else 0
        
        # Door usage patterns
        door_distribution = user_data['door_id'].value_counts()
        door_concentration = self._calculate_concentration_index(door_distribution.values)
        
        # Failure analysis
        failed_attempts = user_data[user_data['access_result'] == 'Denied']
        failure_pattern = self._analyze_user_failures(failed_attempts)
        
        # Risk scoring
        risk_score = self._calculate_user_risk_score(user_data, full_df)
        
        # Behavior classification
        behavior_type = self._classify_user_behavior(user_data, full_df)
        
        return {
            'basic_stats': {
                'total_events': total_events,
                'unique_doors_accessed': unique_doors,
                'success_rate': success_rate,
                'activity_span_days': activity_span,
                'avg_daily_events': total_events / max(activity_span, 1)
            },
            'temporal_patterns': {
                'preferred_hours': preferred_hours,
                'preferred_days': preferred_days,
                'after_hours_events': after_hours_events,
                'weekend_events': weekend_events,
                'activity_consistency': activity_consistency
            },
            'location_patterns': {
                'door_distribution': door_distribution.to_dict(),
                'door_concentration_index': door_concentration,
                'primary_doors': door_distribution.head(3).index.tolist()
            },
            'failure_analysis': failure_pattern,
            'risk_assessment': {
                'risk_score': risk_score,
                'risk_level': self._categorize_risk(risk_score)
            },
            'behavior_classification': {
                'type': behavior_type,
                'confidence': self._calculate_classification_confidence(user_data)
            },
            'anomalies': self._detect_user_anomalies(user_data, full_df)
        }
    
    def _perform_behavior_clustering(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Perform clustering analysis on user behaviors"""
        
        # Create feature matrix for clustering
        user_features = self._extract_user_features(df)
        
        if len(user_features) < 3:
            return {'clusters': {}, 'cluster_count': 0, 'silhouette_score': 0}
        
        # Standardize features
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(user_features.values)
        
        # Determine optimal number of clusters
        optimal_clusters = min(5, max(2, len(user_features) // 3))
        
        # Perform clustering
        kmeans = KMeans(n_clusters=optimal_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(features_scaled)
        
        # Analyze clusters
        user_features['cluster'] = cluster_labels
        cluster_analysis = self._analyze_clusters(user_features, df)
        
        return {
            'cluster_count': optimal_clusters,
            'cluster_analysis': cluster_analysis,
            'cluster_centroids': kmeans.cluster_centers_.tolist(),
            'user_cluster_assignments': user_features[['cluster']].to_dict()
        }
    
    def _extract_user_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract features for clustering analysis"""
        user_features = df.groupby('person_id').agg({
            'event_id': 'count',  # Total activity
            'door_id': 'nunique',  # Door diversity
            'hour': lambda x: x.std(),  # Time consistency
            'is_weekend': 'mean',  # Weekend activity rate
            'is_business_hours': 'mean',  # Business hours rate
            'access_result': lambda x: (x == 'Granted').mean()  # Success rate
        })
        
        user_features.columns = [
            'total_events', 'unique_doors', 'time_variability', 
            'weekend_rate', 'business_hours_rate', 'success_rate'
        ]
        
        # Add derived features
        user_features['events_per_door'] = user_features['total_events'] / user_features['unique_doors']
        user_features['regularity_score'] = 1 - user_features['time_variability'] / 12  # Normalize by max hour std
        
        return user_features.fillna(0)
    
    def _analyze_access_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze detailed access patterns"""
        
        # Sequential access analysis
        df_sorted = df.sort_values(['person_id', 'timestamp'])
        df_sorted['time_diff'] = df_sorted.groupby('person_id')['timestamp'].diff()
        
        # Access frequency patterns
        user_frequencies = df.groupby('person_id').agg({
            'event_id': 'count',
            'timestamp': lambda x: (x.max() - x.min()).days
        })
        user_frequencies['frequency'] = user_frequencies['event_id'] / (user_frequencies['timestamp'] + 1)
        
        # Common access sequences
        access_sequences = self._identify_access_sequences(df_sorted)
        
        # Multi-door sessions
        multi_door_sessions = self._analyze_multi_door_sessions(df_sorted)
        
        return {
            'frequency_distribution': user_frequencies['frequency'].describe().to_dict(),
            'access_sequences': access_sequences,
            'multi_door_sessions': multi_door_sessions,
            'pattern_consistency': self._measure_pattern_consistency(df)
        }
    
    def _analyze_temporal_behavior(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze temporal behavior patterns"""
        
        # Individual time preference analysis
        user_time_patterns = {}
        
        for user_id in df['person_id'].unique():
            user_data = df[df['person_id'] == user_id]
            
            # Preferred time ranges
            hour_distribution = user_data['hour'].value_counts()
            peak_hours = hour_distribution.nlargest(3).index.tolist()
            
            # Day patterns
            day_distribution = user_data['day_of_week'].value_counts()
            preferred_days = day_distribution.nlargest(2).index.tolist()
            
            # Regularity analysis
            daily_counts = user_data.groupby('date')['event_id'].count()
            regularity_score = self._calculate_regularity_score(daily_counts)
            
            user_time_patterns[user_id] = {
                'peak_hours': peak_hours,
                'preferred_days': preferred_days,
                'regularity_score': regularity_score,
                'time_spread': user_data['hour'].std()
            }
        
        # Aggregate temporal insights
        all_users_regularity = [patterns['regularity_score'] for patterns in user_time_patterns.values()]
        
        return {
            'individual_patterns': user_time_patterns,
            'average_regularity': np.mean(all_users_regularity),
            'regularity_distribution': pd.Series(all_users_regularity).describe().to_dict(),
            'temporal_diversity': self._calculate_temporal_diversity(df)
        }
    
    def _analyze_location_preferences(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze user location preferences and mobility"""
        
        location_analysis = {}
        
        for user_id in df['person_id'].unique():
            user_data = df[df['person_id'] == user_id]
            
            # Door preferences
            door_counts = user_data['door_id'].value_counts()
            primary_door = door_counts.index[0] if len(door_counts) > 0 else None
            door_diversity = len(door_counts)
            
            # Mobility score (Shannon entropy of door usage)
            if len(door_counts) > 1:
                probabilities = door_counts / door_counts.sum()
                mobility_score = -np.sum(probabilities * np.log2(probabilities))
            else:
                mobility_score = 0
            
            # Access concentration
            concentration_ratio = door_counts.iloc[0] / door_counts.sum() if len(door_counts) > 0 else 1
            
            location_analysis[user_id] = {
                'primary_door': primary_door,
                'door_diversity': door_diversity,
                'mobility_score': mobility_score,
                'concentration_ratio': concentration_ratio,
                'door_distribution': door_counts.to_dict()
            }
        
        # Aggregate location insights
        mobility_scores = [analysis['mobility_score'] for analysis in location_analysis.values()]
        diversity_scores = [analysis['door_diversity'] for analysis in location_analysis.values()]
        
        return {
            'individual_preferences': location_analysis,
            'average_mobility': np.mean(mobility_scores),
            'average_door_diversity': np.mean(diversity_scores),
            'mobility_distribution': pd.Series(mobility_scores).describe().to_dict()
        }
    
    def _detect_behavioral_anomalies(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect behavioral anomalies using statistical methods"""
        
        anomalies = {
            'user_anomalies': {},
            'temporal_anomalies': [],
            'access_anomalies': [],
            'pattern_breaks': []
        }
        
        # User-level anomalies
        for user_id in df['person_id'].unique():
            user_data = df[df['person_id'] == user_id]
            user_anomalies = self._detect_user_anomalies(user_data, df)
            if user_anomalies:
                anomalies['user_anomalies'][user_id] = user_anomalies
        
        # Temporal anomalies (unusual time patterns)
        temporal_anomalies = self._detect_temporal_anomalies(df)
        anomalies['temporal_anomalies'] = temporal_anomalies
        
        # Access pattern anomalies
        access_anomalies = self._detect_access_pattern_anomalies(df)
        anomalies['access_anomalies'] = access_anomalies
        
        return anomalies
    
    def _segment_users(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Segment users based on behavior patterns"""
        
        segments = {
            'power_users': [],
            'regular_users': [],
            'occasional_users': [],
            'irregular_users': [],
            'security_risks': []
        }
        
        user_stats = df.groupby('person_id').agg({
            'event_id': 'count',
            'door_id': 'nunique',
            'access_result': lambda x: (x == 'Granted').mean(),
            'timestamp': lambda x: (x.max() - x.min()).days
        })
        
        # Define segmentation criteria
        high_activity_threshold = user_stats['event_id'].quantile(0.8)
        low_activity_threshold = user_stats['event_id'].quantile(0.2)
        
        for user_id, stats in user_stats.iterrows():
            user_data = df[df['person_id'] == user_id]
            
            # Classify user
            if stats['event_id'] >= high_activity_threshold:
                if stats['access_result'] > 0.9:
                    segments['power_users'].append(user_id)
                else:
                    segments['security_risks'].append(user_id)
            elif stats['event_id'] >= low_activity_threshold:
                if self._is_regular_pattern(user_data):
                    segments['regular_users'].append(user_id)
                else:
                    segments['irregular_users'].append(user_id)
            else:
                segments['occasional_users'].append(user_id)
        
        # Add segment statistics
        segment_stats = {}
        for segment, users in segments.items():
            if users:
                segment_data = df[df['person_id'].isin(users)]
                segment_stats[segment] = {
                    'user_count': len(users),
                    'avg_events_per_user': len(segment_data) / len(users),
                    'avg_success_rate': (segment_data['access_result'] == 'Granted').mean() * 100,
                    'total_events': len(segment_data)
                }
            else:
                segment_stats[segment] = {
                    'user_count': 0,
                    'avg_events_per_user': 0,
                    'avg_success_rate': 0,
                    'total_events': 0
                }
        
        return {
            'segments': segments,
            'segment_statistics': segment_stats,
            'segmentation_summary': self._summarize_segmentation(segment_stats)
        }
    
    def _generate_behavior_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate comprehensive behavior summary"""

        total_users = df['person_id'].nunique()

        if total_users == 0:
            return {
                'total_unique_users': 0,
                'avg_events_per_user': 0,
                'overall_success_rate': 0,
                'behavior_diversity': {
                    'avg_hour_diversity': 0,
                    'avg_door_diversity': 0
                },
                'activity_distribution': {
                    'weekend_active_users': 0,
                    'after_hours_users': 0,
                    'weekend_participation_rate': 0,
                    'after_hours_participation_rate': 0
                },
                'risk_indicators': {
                    'high_failure_users': 0,
                    'risk_user_percentage': 0
                },
                'key_insights': []
            }

        # Overall behavior metrics
        avg_events_per_user = len(df) / total_users
        overall_success_rate = (df['access_result'] == 'Granted').mean() * 100

        # Behavior diversity
        user_hour_diversity = df.groupby('person_id')['hour'].nunique().mean()
        user_door_diversity = df.groupby('person_id')['door_id'].nunique().mean()

        # Activity patterns
        weekend_users = df[df['is_weekend']]['person_id'].nunique()
        after_hours_users = df[~df['is_business_hours']]['person_id'].nunique()

        # Risk indicators
        high_failure_users = df.groupby('person_id').agg({
            'access_result': lambda x: (x == 'Denied').sum()
        })
        risky_users = len(high_failure_users[high_failure_users['access_result'] >= 5])

        return {
            'total_unique_users': total_users,
            'avg_events_per_user': avg_events_per_user,
            'overall_success_rate': overall_success_rate,
            'behavior_diversity': {
                'avg_hour_diversity': user_hour_diversity,
                'avg_door_diversity': user_door_diversity
            },
            'activity_distribution': {
                'weekend_active_users': weekend_users,
                'after_hours_users': after_hours_users,
                'weekend_participation_rate': weekend_users / total_users * 100,
                'after_hours_participation_rate': after_hours_users / total_users * 100
            },
            'risk_indicators': {
                'high_failure_users': risky_users,
                'risk_user_percentage': risky_users / total_users * 100
            },
            'key_insights': self._generate_behavior_insights(df)
        }
    
    # Helper methods
    def _calculate_concentration_index(self, values: np.ndarray) -> float:
        """Calculate Herfindahl-Hirschman Index for concentration"""
        if len(values) == 0:
            return 0
        
        total = values.sum()
        if total == 0:
            return 0
        
        shares = values / total
        hhi = np.sum(shares ** 2)
        return hhi
    
    def _analyze_user_failures(self, failed_attempts: pd.DataFrame) -> Dict[str, Any]:
        """Analyze user-specific failure patterns"""
        if failed_attempts.empty:
            return {'total_failures': 0, 'failure_pattern': 'none'}
        
        failure_hours = failed_attempts['hour'].value_counts()
        failure_doors = failed_attempts['door_id'].value_counts()
        
        return {
            'total_failures': len(failed_attempts),
            'failure_hours': failure_hours.to_dict(),
            'failure_doors': failure_doors.to_dict(),
            'failure_concentration': len(failure_doors) == 1  # All failures at one door
        }
    
    def _calculate_user_risk_score(self, user_data: pd.DataFrame, 
                                   full_df: pd.DataFrame) -> float:
        """Calculate risk score for user (0-100, higher = more risky)"""
        
        risk_score = 0
        
        # Failure rate component
        failure_rate = (user_data['access_result'] == 'Denied').mean()
        risk_score += failure_rate * 40
        
        # After-hours activity component
        after_hours_rate = (~user_data['is_business_hours']).mean()
        risk_score += after_hours_rate * 20
        
        # Badge issues component
        if 'badge_status' in user_data.columns:
            badge_issue_rate = (user_data['badge_status'] != 'Valid').mean()
            risk_score += badge_issue_rate * 30
        
        # Unusual pattern component
        if self._has_unusual_patterns(user_data, full_df):
            risk_score += 10
        
        return min(100, risk_score)
    
    def _classify_user_behavior(self, user_data: pd.DataFrame, 
                                full_df: pd.DataFrame) -> str:
        """Classify user behavior type"""
        
        total_events = len(user_data)
        activity_span = (user_data['timestamp'].max() - user_data['timestamp'].min()).days
        avg_daily = total_events / max(activity_span, 1)
        
        # Get percentiles from full dataset
        all_user_events = full_df.groupby('person_id')['event_id'].count()
        user_percentile = (all_user_events <= total_events).mean()
        
        # Classification logic
        if user_percentile >= 0.9:
            return 'power_user'
        elif user_percentile >= 0.7:
            if self._is_regular_pattern(user_data):
                return 'regular_user'
            else:
                return 'irregular_user'
        elif user_percentile >= 0.3:
            return 'moderate_user'
        else:
            return 'occasional_user'
    
    def _calculate_classification_confidence(self, user_data: pd.DataFrame) -> float:
        """Calculate confidence in behavior classification"""
        
        # More data = higher confidence
        data_confidence = min(1.0, len(user_data) / 50)
        
        # Pattern consistency = higher confidence
        daily_counts = user_data.groupby('date')['event_id'].count()
        if len(daily_counts) > 1:
            consistency = 1 - (daily_counts.std() / daily_counts.mean())
            consistency = max(0, min(1, consistency))
        else:
            consistency = 0.5
        
        return (data_confidence + consistency) / 2
    
    def _detect_user_anomalies(self, user_data: pd.DataFrame, 
                               full_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect anomalies for specific user"""
        
        anomalies = []
        
        # Unusual time patterns
        user_hours = user_data['hour'].values
        typical_hours = full_df['hour'].values
        
        # Statistical test for time pattern deviation
        if len(user_hours) >= 5:
            _, p_value = stats.ks_2samp(user_hours, typical_hours)
            if p_value < 0.05:
                anomalies.append({
                    'type': 'unusual_time_pattern',
                    'significance': p_value,
                    'description': 'User has significantly different time patterns'
                })
        
        # Excessive failures
        failure_rate = (user_data['access_result'] == 'Denied').mean()
        overall_failure_rate = (full_df['access_result'] == 'Denied').mean()
        
        if failure_rate > overall_failure_rate * 3 and failure_rate > 0.1:
            anomalies.append({
                'type': 'high_failure_rate',
                'user_rate': failure_rate,
                'system_rate': overall_failure_rate,
                'description': f'User failure rate ({failure_rate:.1%}) is {failure_rate/overall_failure_rate:.1f}x system average'
            })
        
        return anomalies
    
    def _analyze_clusters(self, user_features: pd.DataFrame, 
                          df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze the characteristics of each cluster"""
        
        cluster_analysis = {}
        
        for cluster_id in user_features['cluster'].unique():
            cluster_users = user_features[user_features['cluster'] == cluster_id].index
            cluster_data = df[df['person_id'].isin(cluster_users)]
            
            # Cluster characteristics
            cluster_features = user_features[user_features['cluster'] == cluster_id]
            
            cluster_analysis[f'cluster_{cluster_id}'] = {
                'user_count': len(cluster_users),
                'avg_total_events': cluster_features['total_events'].mean(),
                'avg_unique_doors': cluster_features['unique_doors'].mean(),
                'avg_success_rate': cluster_features['success_rate'].mean(),
                'avg_weekend_rate': cluster_features['weekend_rate'].mean(),
                'cluster_description': self._describe_cluster(cluster_features)
            }
        
        return cluster_analysis
    
    def _describe_cluster(self, cluster_features: pd.DataFrame) -> str:
        """Generate description for cluster characteristics"""
        
        avg_events = cluster_features['total_events'].mean()
        avg_success = cluster_features['success_rate'].mean()
        avg_weekend = cluster_features['weekend_rate'].mean()
        avg_business = cluster_features['business_hours_rate'].mean()
        
        # Generate description based on characteristics
        if avg_events > 100:
            activity_level = "High activity"
        elif avg_events > 20:
            activity_level = "Moderate activity"
        else:
            activity_level = "Low activity"
        
        if avg_business > 0.8:
            timing = "business hours focused"
        elif avg_weekend > 0.3:
            timing = "frequent weekend activity"
        else:
            timing = "mixed timing"
        
        if avg_success > 0.95:
            success_level = "high success rate"
        elif avg_success > 0.8:
            success_level = "moderate success rate"
        else:
            success_level = "low success rate"
        
        return f"{activity_level} users with {timing} and {success_level}"
    
    def _identify_access_sequences(self, df_sorted: pd.DataFrame) -> Dict[str, Any]:
        """Identify common access sequences"""
        
        sequences = {}
        
        # Look for door sequences within short time windows
        for user_id in df_sorted['person_id'].unique():
            user_data = df_sorted[df_sorted['person_id'] == user_id].copy()
            user_data['time_diff'] = user_data['timestamp'].diff()
            
            # Group events within 30 minutes as potential sequences
            user_data['session'] = (user_data['time_diff'] > pd.Timedelta(minutes=30)).cumsum()
            
            for session_id in user_data['session'].unique():
                session_data = user_data[user_data['session'] == session_id]
                if len(session_data) > 1:
                    door_sequence = tuple(session_data['door_id'].values)
                    if door_sequence not in sequences:
                        sequences[door_sequence] = 0
                    sequences[door_sequence] += 1
        
        # Return most common sequences
        common_sequences = sorted(sequences.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'common_sequences': common_sequences,
            'total_sequences': len(sequences),
            'sequence_diversity': len(sequences) / max(sum(sequences.values()), 1)
        }
    
    def _analyze_multi_door_sessions(self, df_sorted: pd.DataFrame) -> Dict[str, Any]:
        """Analyze sessions involving multiple doors"""
        
        multi_door_sessions = []
        
        for user_id in df_sorted['person_id'].unique():
            user_data = df_sorted[df_sorted['person_id'] == user_id].copy()
            user_data['time_diff'] = user_data['timestamp'].diff()
            
            # Define sessions (gaps > 30 minutes start new session)
            user_data['session'] = (user_data['time_diff'] > pd.Timedelta(minutes=30)).cumsum()
            
            session_stats = user_data.groupby('session').agg({
                'door_id': 'nunique',
                'event_id': 'count',
                'timestamp': ['min', 'max']
            })
            
            # Focus on multi-door sessions
            multi_door = session_stats[session_stats[('door_id', 'nunique')] > 1]
            multi_door_sessions.extend(multi_door.values.tolist())
        
        if multi_door_sessions:
            avg_doors_per_session = np.mean([session[0] for session in multi_door_sessions])
            avg_events_per_session = np.mean([session[1] for session in multi_door_sessions])
        else:
            avg_doors_per_session = 0
            avg_events_per_session = 0
        
        return {
            'total_multi_door_sessions': len(multi_door_sessions),
            'avg_doors_per_session': avg_doors_per_session,
            'avg_events_per_session': avg_events_per_session
        }
    
    def _measure_pattern_consistency(self, df: pd.DataFrame) -> Dict[str, float]:
        """Measure how consistent user patterns are"""
        
        consistency_scores = {}
        
        for user_id in df['person_id'].unique():
            user_data = df[df['person_id'] == user_id]
            
            if len(user_data) < 3:
                consistency_scores[user_id] = 0
                continue
            
            # Time consistency
            hourly_pattern = user_data['hour'].value_counts(normalize=True)
            time_entropy = -np.sum(hourly_pattern * np.log2(hourly_pattern + 1e-10))
            time_consistency = 1 - (time_entropy / np.log2(24))  # Normalize by max entropy
            
            # Door consistency
            door_pattern = user_data['door_id'].value_counts(normalize=True)
            door_entropy = -np.sum(door_pattern * np.log2(door_pattern + 1e-10))
            max_door_entropy = np.log2(user_data['door_id'].nunique())
            door_consistency = 1 - (door_entropy / max_door_entropy) if max_door_entropy > 0 else 1
            
            # Combined consistency
            consistency_scores[user_id] = (time_consistency + door_consistency) / 2
        
        return {
            'individual_scores': consistency_scores,
            'average_consistency': np.mean(list(consistency_scores.values())),
            'consistency_std': np.std(list(consistency_scores.values()))
        }
    
    def _calculate_regularity_score(self, daily_counts: pd.Series) -> float:
        """Calculate regularity score based on daily activity"""
        
        if len(daily_counts) < 2:
            return 0
        
        # Coefficient of variation (lower = more regular)
        cv = daily_counts.std() / daily_counts.mean() if daily_counts.mean() > 0 else float('inf')
        
        # Convert to 0-1 score (higher = more regular)
        regularity = 1 / (1 + cv)
        
        return regularity
    
    def _calculate_temporal_diversity(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate temporal diversity metrics"""
        
        # Hour diversity (Shannon entropy)
        hour_dist = df['hour'].value_counts(normalize=True)
        hour_entropy = -np.sum(hour_dist * np.log2(hour_dist + 1e-10))
        hour_diversity = hour_entropy / np.log2(24)  # Normalize
        
        # Day diversity
        day_dist = df['day_of_week'].value_counts(normalize=True)
        day_entropy = -np.sum(day_dist * np.log2(day_dist + 1e-10))
        day_diversity = day_entropy / np.log2(7)  # Normalize
        
        return {
            'hour_diversity': hour_diversity,
            'day_diversity': day_diversity,
            'overall_temporal_diversity': (hour_diversity + day_diversity) / 2
        }
    
    def _detect_temporal_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect temporal anomalies in access patterns"""
        
        anomalies = []
        
        # Unusual hour activity
        hour_counts = df['hour'].value_counts()
        hour_mean = hour_counts.mean()
        hour_std = hour_counts.std()
        
        for hour, count in hour_counts.items():
            z_score = abs(count - hour_mean) / hour_std if hour_std > 0 else 0
            if z_score > 2.5:  # Significant deviation
                anomalies.append({
                    'type': 'unusual_hour_activity',
                    'hour': hour,
                    'event_count': count,
                    'z_score': z_score,
                    'severity': 'high' if z_score > 3 else 'medium'
                })
        
        return anomalies
    
    def _detect_access_pattern_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect access pattern anomalies"""
        
        anomalies = []
        
        # Rapid successive attempts
        df_sorted = df.sort_values(['person_id', 'timestamp'])
        df_sorted['time_diff'] = df_sorted.groupby('person_id')['timestamp'].diff()
        
        rapid_attempts = df_sorted[df_sorted['time_diff'] < pd.Timedelta(minutes=1)]
        
        if len(rapid_attempts) > 0:
            anomalies.append({
                'type': 'rapid_successive_attempts',
                'count': len(rapid_attempts),
                'affected_users': rapid_attempts['person_id'].nunique(),
                'description': 'Multiple access attempts within 1 minute'
            })
        
        return anomalies
    
    def _categorize_risk(self, risk_score: float) -> str:
        """Categorize risk level based on score"""
        if risk_score >= 70:
            return 'high'
        elif risk_score >= 40:
            return 'medium'
        elif risk_score >= 20:
            return 'low'
        else:
            return 'minimal'
    
    def _has_unusual_patterns(self, user_data: pd.DataFrame, 
                              full_df: pd.DataFrame) -> bool:
        """Check if user has unusual patterns compared to population"""
        
        # Simple heuristic checks
        user_after_hours_rate = (~user_data['is_business_hours']).mean()
        system_after_hours_rate = (~full_df['is_business_hours']).mean()
        
        user_weekend_rate = user_data['is_weekend'].mean()
        system_weekend_rate = full_df['is_weekend'].mean()
        
        # Consider unusual if rates are significantly higher than system average
        return (user_after_hours_rate > system_after_hours_rate * 3 or
                user_weekend_rate > system_weekend_rate * 3)
    
    def _is_regular_pattern(self, user_data: pd.DataFrame) -> bool:
        """Check if user has regular access patterns"""
        
        if len(user_data) < 3:
            return False
        
        # Check time consistency
        hour_std = user_data['hour'].std()
        time_regular = hour_std < 4  # Within 4-hour standard deviation
        
        # Check frequency consistency
        daily_counts = user_data.groupby('date')['event_id'].count()
        if len(daily_counts) > 1:
            freq_cv = daily_counts.std() / daily_counts.mean()
            freq_regular = freq_cv < 1  # Coefficient of variation < 1
        else:
            freq_regular = True
        
        return time_regular and freq_regular
    
    def _summarize_segmentation(self, segment_stats: Dict[str, Dict]) -> Dict[str, Any]:
        """Summarize user segmentation results"""
        
        total_users = sum(stats['user_count'] for stats in segment_stats.values())
        
        if total_users == 0:
            return {'dominant_segment': 'none', 'distribution': {}}
        
        # Calculate segment distribution
        distribution = {
            segment: stats['user_count'] / total_users * 100
            for segment, stats in segment_stats.items()
        }
        
        # Find dominant segment
        dominant_segment = max(distribution.items(), key=lambda x: x[1])[0]
        
        return {
            'dominant_segment': dominant_segment,
            'distribution_percentages': distribution,
            'segmentation_quality': self._assess_segmentation_quality(distribution)
        }
    
    def _assess_segmentation_quality(self, distribution: Dict[str, float]) -> str:
        """Assess quality of segmentation"""
        
        # Calculate entropy of distribution
        probs = [p/100 for p in distribution.values() if p > 0]
        entropy = -sum(p * np.log2(p) for p in probs)
        max_entropy = np.log2(len(probs))
        
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
        
        if normalized_entropy > 0.8:
            return 'well_distributed'
        elif normalized_entropy > 0.5:
            return 'moderately_distributed'
        else:
            return 'concentrated'
    
    def _generate_behavior_insights(self, df: pd.DataFrame) -> List[str]:
        """Generate key insights about user behavior"""
        
        insights = []
        
        total_users = df['person_id'].nunique()
        
        # Activity level insight
        user_events = df.groupby('person_id')['event_id'].count()
        high_activity_users = len(user_events[user_events > user_events.quantile(0.8)])
        insights.append(f"{high_activity_users} users ({high_activity_users/total_users*100:.1f}%) are high-activity users")
        
        # Time pattern insight
        after_hours_users = df[~df['is_business_hours']]['person_id'].nunique()
        if after_hours_users > total_users * 0.1:
            insights.append(f"Significant after-hours activity: {after_hours_users} users")
        
        # Success rate insight
        user_success_rates = df.groupby('person_id').agg({
            'access_result': lambda x: (x == 'Granted').mean()
        })['access_result']
        
        low_success_users = len(user_success_rates[user_success_rates < 0.8])
        if low_success_users > 0:
            insights.append(f"{low_success_users} users have success rates below 80%")
        
        # Door diversity insight
        user_door_diversity = df.groupby('person_id')['door_id'].nunique()
        high_mobility_users = len(user_door_diversity[user_door_diversity > 5])
        if high_mobility_users > 0:
            insights.append(f"{high_mobility_users} users access more than 5 different doors")
        
        return insights
    
    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result structure"""
        return {
            'user_profiles': {},
            'behavior_clustering': {'clusters': {}, 'cluster_count': 0},
            'access_patterns': {'frequency_distribution': {}},
            'temporal_behavior': {'individual_patterns': {}},
            'location_preferences': {'individual_preferences': {}},
            'behavioral_anomalies': {'user_anomalies': {}},
            'user_segments': {'segments': {}, 'segment_statistics': {}},
            'behavior_summary': {'total_unique_users': 0}
        }

# Factory function
def create_behavior_analyzer() -> UserBehaviorAnalyzer:
    """Create user behavior analyzer instance"""
    return UserBehaviorAnalyzer()

# Export
__all__ = ['UserBehaviorAnalyzer', 'UserProfile', 'create_behavior_analyzer']
