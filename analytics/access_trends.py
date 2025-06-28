"""
Access Trends Analytics Module
Analyzes temporal and usage trends in access control data
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
import logging
from scipy import stats
from sklearn.linear_model import LinearRegression

@dataclass
class TrendMetrics:
    """Trend metrics data structure"""
    metric_name: str
    trend_direction: str  # 'increasing', 'decreasing', 'stable'
    trend_strength: float  # 0-1
    percentage_change: float
    significance: str  # 'high', 'medium', 'low'
    period_comparison: Dict[str, float]

class AccessTrendsAnalyzer:
    """Advanced access trends analysis"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def analyze_trends(self, df: pd.DataFrame, 
                       comparison_period_days: int = 30) -> Dict[str, Any]:
        """Main analysis function for access trends"""
        try:
            if df.empty:
                return self._empty_result()
            
            df = self._prepare_data(df)
            
            trends = {
                'temporal_trends': self._analyze_temporal_trends(df),
                'volume_trends': self._analyze_volume_trends(df),
                'usage_patterns': self._analyze_usage_patterns(df),
                'peak_analysis': self._analyze_peak_periods(df),
                'growth_metrics': self._calculate_growth_metrics(df),
                'seasonal_patterns': self._analyze_seasonal_patterns(df),
                'forecasting': self._generate_forecasts(df),
                'trend_summary': self._generate_trend_summary(df)
            }
            
            return trends
            
        except Exception as e:
            self.logger.error(f"Access trends analysis failed: {e}")
            return self._empty_result()
    
    def _prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare and validate data for trend analysis"""
        df = df.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.day_name()
        df['week'] = df['timestamp'].dt.isocalendar().week
        df['month'] = df['timestamp'].dt.month
        df['is_weekend'] = df['timestamp'].dt.weekday >= 5
        df['quarter_hour'] = (df['timestamp'].dt.minute // 15) * 15
        return df
    
    def _analyze_temporal_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze temporal trends (hourly, daily, weekly)"""
        
        # Hourly trends
        hourly_data = df.groupby('hour').agg({
            'event_id': 'count',
            'access_result': lambda x: (x == 'Granted').mean() * 100
        }).rename(columns={'event_id': 'event_count', 'access_result': 'success_rate'})
        
        # Daily trends
        daily_data = df.groupby('date').agg({
            'event_id': 'count',
            'person_id': 'nunique',
            'door_id': 'nunique',
            'access_result': lambda x: (x == 'Granted').mean() * 100
        })
        
        # Weekly trends
        weekly_data = df.groupby('day_of_week').agg({
            'event_id': 'count',
            'access_result': lambda x: (x == 'Granted').mean() * 100
        })
        
        # Calculate trend directions
        hourly_trend = self._calculate_trend_direction(hourly_data['event_count'].values)
        daily_trend = self._calculate_trend_direction(daily_data['event_id'].values)
        
        return {
            'hourly_distribution': hourly_data.to_dict(),
            'daily_distribution': daily_data.to_dict(),
            'weekly_distribution': weekly_data.to_dict(),
            'hourly_trend': hourly_trend,
            'daily_trend': daily_trend,
            'peak_hours': self._identify_peak_hours(hourly_data),
            'trend_metrics': self._calculate_temporal_metrics(df)
        }
    
    def _analyze_volume_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze access volume trends over time"""
        
        # Daily volume analysis
        daily_volumes = df.groupby('date').agg({
            'event_id': 'count',
            'person_id': 'nunique',
            'door_id': 'nunique'
        }).rename(columns={'event_id': 'total_events', 'person_id': 'unique_users', 'door_id': 'unique_doors'})
        
        # Rolling averages
        daily_volumes['7day_avg'] = daily_volumes['total_events'].rolling(window=7).mean()
        daily_volumes['30day_avg'] = daily_volumes['total_events'].rolling(window=30).mean()
        
        # Calculate growth rates
        daily_volumes['daily_growth'] = daily_volumes['total_events'].pct_change() * 100
        daily_volumes['weekly_growth'] = daily_volumes['7day_avg'].pct_change(periods=7) * 100
        
        # Volume statistics
        volume_stats = {
            'avg_daily_events': daily_volumes['total_events'].mean(),
            'max_daily_events': daily_volumes['total_events'].max(),
            'min_daily_events': daily_volumes['total_events'].min(),
            'std_daily_events': daily_volumes['total_events'].std(),
            'trend_direction': self._calculate_trend_direction(daily_volumes['total_events'].values),
            'volatility': daily_volumes['total_events'].std() / daily_volumes['total_events'].mean()
        }
        
        return {
            'daily_volumes': daily_volumes.to_dict(),
            'volume_statistics': volume_stats,
            'growth_analysis': self._analyze_growth_patterns(daily_volumes),
            'volume_anomalies': self._detect_volume_anomalies(daily_volumes)
        }
    
    def _analyze_usage_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze usage patterns by users and doors"""
        
        # User usage patterns
        user_patterns = df.groupby('person_id').agg({
            'event_id': 'count',
            'door_id': 'nunique',
            'timestamp': ['min', 'max'],
            'access_result': lambda x: (x == 'Granted').mean() * 100
        })
        user_patterns.columns = ['total_events', 'doors_accessed', 'first_access', 'last_access', 'success_rate']
        
        # Door usage patterns
        door_patterns = df.groupby('door_id').agg({
            'event_id': 'count',
            'person_id': 'nunique',
            'timestamp': lambda x: x.dt.hour.mode().iloc[0] if len(x) > 0 else 0,
            'access_result': lambda x: (x == 'Granted').mean() * 100
        })
        door_patterns.columns = ['total_events', 'unique_users', 'peak_hour', 'success_rate']
        
        # Usage distribution analysis
        usage_distribution = {
            'heavy_users': len(user_patterns[user_patterns['total_events'] > user_patterns['total_events'].quantile(0.9)]),
            'light_users': len(user_patterns[user_patterns['total_events'] < user_patterns['total_events'].quantile(0.25)]),
            'active_doors': len(door_patterns[door_patterns['total_events'] > 0]),
            'high_traffic_doors': len(door_patterns[door_patterns['total_events'] > door_patterns['total_events'].quantile(0.8)])
        }
        
        return {
            'user_patterns': user_patterns.head(20).to_dict(),
            'door_patterns': door_patterns.to_dict(),
            'usage_distribution': usage_distribution,
            'access_concentration': self._analyze_access_concentration(df),
            'user_loyalty': self._analyze_user_loyalty(user_patterns)
        }
    
    def _analyze_peak_periods(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze peak access periods"""
        
        # Hourly peak analysis
        hourly_counts = df.groupby('hour')['event_id'].count()
        peak_hours = hourly_counts.nlargest(3).index.tolist()
        
        # Daily peak analysis
        daily_counts = df.groupby('day_of_week')['event_id'].count()
        peak_days = daily_counts.nlargest(2).index.tolist()
        
        # Quarter-hour granularity for precise peak identification
        df['hour_quarter'] = df['hour'].astype(str) + ':' + df['quarter_hour'].astype(str).str.zfill(2)
        quarter_hour_counts = df.groupby('hour_quarter')['event_id'].count()
        precise_peaks = quarter_hour_counts.nlargest(5)
        
        # Peak intensity analysis
        peak_intensity = self._calculate_peak_intensity(df)
        
        # Peak consistency (how consistent are the peaks day-to-day)
        peak_consistency = self._analyze_peak_consistency(df)
        
        return {
            'peak_hours': peak_hours,
            'peak_days': peak_days,
            'precise_peak_times': precise_peaks.to_dict(),
            'peak_intensity_score': peak_intensity,
            'peak_consistency': peak_consistency,
            'off_peak_analysis': self._analyze_off_peak_periods(df)
        }
    
    def _calculate_growth_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate various growth metrics"""
        
        daily_data = df.groupby('date')['event_id'].count()
        
        # Period-over-period growth
        if len(daily_data) >= 14:
            first_week = daily_data.head(7).mean()
            last_week = daily_data.tail(7).mean()
            weekly_growth = ((last_week - first_week) / first_week) * 100
        else:
            weekly_growth = 0
        
        # Month-over-month (if enough data)
        monthly_growth = 0
        if len(daily_data) >= 60:
            first_month = daily_data.head(30).mean()
            last_month = daily_data.tail(30).mean()
            monthly_growth = ((last_month - first_month) / first_month) * 100
        
        # Compound Annual Growth Rate (CAGR) approximation
        if len(daily_data) >= 30:
            periods = len(daily_data) / 365.25  # Convert days to years
            beginning_value = daily_data.head(7).mean()
            ending_value = daily_data.tail(7).mean()
            cagr = ((ending_value / beginning_value) ** (1/periods) - 1) * 100
        else:
            cagr = 0
        
        return {
            'weekly_growth_rate': weekly_growth,
            'monthly_growth_rate': monthly_growth,
            'annualized_growth_rate': cagr,
            'growth_trend': 'positive' if weekly_growth > 0 else 'negative' if weekly_growth < 0 else 'stable',
            'growth_acceleration': self._calculate_growth_acceleration(daily_data)
        }
    
    def _analyze_seasonal_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze seasonal and cyclical patterns"""
        
        # Day of week patterns
        dow_patterns = df.groupby('day_of_week')['event_id'].count()
        weekend_vs_weekday = {
            'weekday_avg': df[~df['is_weekend']].groupby('date')['event_id'].count().mean(),
            'weekend_avg': df[df['is_weekend']].groupby('date')['event_id'].count().mean()
        }
        
        # Monthly patterns (if enough data spans multiple months)
        monthly_patterns = df.groupby('month')['event_id'].count() if df['month'].nunique() > 1 else {}
        
        # Hour-of-day patterns by day type
        weekday_hourly = df[~df['is_weekend']].groupby('hour')['event_id'].count()
        weekend_hourly = df[df['is_weekend']].groupby('hour')['event_id'].count()
        
        return {
            'day_of_week_patterns': dow_patterns.to_dict(),
            'weekend_vs_weekday': weekend_vs_weekday,
            'monthly_patterns': monthly_patterns.to_dict() if hasattr(monthly_patterns, 'to_dict') else {},
            'weekday_hourly_pattern': weekday_hourly.to_dict(),
            'weekend_hourly_pattern': weekend_hourly.to_dict(),
            'seasonal_strength': self._calculate_seasonal_strength(df)
        }
    
    def _generate_forecasts(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate simple trend-based forecasts"""
        
        daily_data = df.groupby('date')['event_id'].count()
        
        if len(daily_data) < 7:
            return {'forecast_available': False, 'reason': 'insufficient_data'}
        
        # Simple linear regression for trend
        X = np.arange(len(daily_data)).reshape(-1, 1)
        y = daily_data.values
        
        model = LinearRegression()
        model.fit(X, y)
        
        # Forecast next 7 days
        future_X = np.arange(len(daily_data), len(daily_data) + 7).reshape(-1, 1)
        forecast = model.predict(future_X)
        
        # Calculate confidence based on R-squared
        r_squared = model.score(X, y)
        confidence = 'high' if r_squared > 0.7 else 'medium' if r_squared > 0.4 else 'low'
        
        return {
            'forecast_available': True,
            'next_7_days_forecast': forecast.tolist(),
            'trend_slope': model.coef_[0],
            'confidence_level': confidence,
            'r_squared': r_squared,
            'forecast_summary': self._summarize_forecast(forecast, daily_data.mean())
        }
    
    def _generate_trend_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate comprehensive trend summary"""
        
        total_events = len(df)
        date_range = (df['timestamp'].max() - df['timestamp'].min()).days
        daily_average = total_events / max(date_range, 1)
        
        # Key trend indicators
        daily_data = df.groupby('date')['event_id'].count()
        trend_direction = self._calculate_trend_direction(daily_data.values)
        
        # Usage intensity
        unique_users = df['person_id'].nunique()
        events_per_user = total_events / unique_users if unique_users > 0 else 0
        
        # Access success trends
        success_rate = (df['access_result'] == 'Granted').mean() * 100
        success_trend = self._analyze_success_rate_trend(df)
        
        return {
            'overall_trend': trend_direction,
            'daily_average_events': daily_average,
            'events_per_user_average': events_per_user,
            'overall_success_rate': success_rate,
            'success_rate_trend': success_trend,
            'data_period_days': date_range,
            'trend_strength': self._calculate_overall_trend_strength(df),
            'key_insights': self._generate_key_insights(df)
        }
    
    # Helper methods
    def _calculate_trend_direction(self, values: np.ndarray) -> Dict[str, Any]:
        """Calculate trend direction using linear regression"""
        if len(values) < 2:
            return {'direction': 'insufficient_data', 'strength': 0}
        
        X = np.arange(len(values)).reshape(-1, 1)
        model = LinearRegression()
        model.fit(X, values)
        
        slope = model.coef_[0]
        r_squared = model.score(X, values)
        
        if abs(slope) < 0.1:
            direction = 'stable'
        elif slope > 0:
            direction = 'increasing'
        else:
            direction = 'decreasing'
        
        strength = min(abs(slope) * r_squared, 1.0)  # Normalize strength
        
        return {
            'direction': direction,
            'strength': strength,
            'slope': slope,
            'r_squared': r_squared
        }
    
    def _identify_peak_hours(self, hourly_data: pd.DataFrame) -> List[int]:
        """Identify peak hours based on event count"""
        return hourly_data['event_count'].nlargest(3).index.tolist()
    
    def _calculate_temporal_metrics(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate various temporal metrics"""
        # Time span utilization
        total_hours = (df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 3600
        active_hours = df['hour'].nunique()
        
        # Distribution metrics
        hour_std = df['hour'].std()
        hour_range = df['hour'].max() - df['hour'].min()
        
        return {
            'time_span_hours': total_hours,
            'active_hours_count': active_hours,
            'hour_distribution_std': hour_std,
            'hour_range': hour_range,
            'temporal_concentration': 1 - (active_hours / 24)  # 0 = spread out, 1 = concentrated
        }
    
    def _analyze_growth_patterns(self, daily_volumes: pd.DataFrame) -> Dict[str, Any]:
        """Analyze growth patterns in detail"""
        growth_rates = daily_volumes['daily_growth'].dropna()
        
        return {
            'average_daily_growth': growth_rates.mean(),
            'growth_volatility': growth_rates.std(),
            'positive_growth_days': (growth_rates > 0).sum(),
            'negative_growth_days': (growth_rates < 0).sum(),
            'max_daily_growth': growth_rates.max(),
            'max_daily_decline': growth_rates.min()
        }
    
    def _detect_volume_anomalies(self, daily_volumes: pd.DataFrame) -> List[Dict]:
        """Detect volume anomalies using statistical methods"""
        volumes = daily_volumes['total_events']
        mean_vol = volumes.mean()
        std_vol = volumes.std()
        
        # Z-score based anomalies
        z_scores = np.abs((volumes - mean_vol) / std_vol)
        anomalies = []
        
        for date, z_score in z_scores.items():
            if z_score > 2.5:  # 2.5 standard deviations
                anomalies.append({
                    'date': str(date),
                    'volume': volumes[date],
                    'z_score': z_score,
                    'type': 'high' if volumes[date] > mean_vol else 'low'
                })
        
        return anomalies
    
    def _analyze_access_concentration(self, df: pd.DataFrame) -> Dict[str, float]:
        """Analyze concentration of access across users and doors"""
        
        # User concentration (Gini coefficient approximation)
        user_counts = df['person_id'].value_counts()
        user_gini = self._calculate_gini_coefficient(user_counts.values)
        
        # Door concentration
        door_counts = df['door_id'].value_counts()
        door_gini = self._calculate_gini_coefficient(door_counts.values)
        
        return {
            'user_concentration_gini': user_gini,
            'door_concentration_gini': door_gini,
            'top_10_percent_users_share': user_counts.head(max(1, len(user_counts) // 10)).sum() / len(df),
            'top_10_percent_doors_share': door_counts.head(max(1, len(door_counts) // 10)).sum() / len(df)
        }
    
    def _analyze_user_loyalty(self, user_patterns: pd.DataFrame) -> Dict[str, Any]:
        """Analyze user loyalty and retention patterns"""
        
        # Days between first and last access
        user_patterns['activity_span'] = (user_patterns['last_access'] - user_patterns['first_access']).dt.days
        
        # Categorize users
        one_time_users = len(user_patterns[user_patterns['total_events'] == 1])
        regular_users = len(user_patterns[user_patterns['total_events'] >= 10])
        power_users = len(user_patterns[user_patterns['total_events'] >= 50])
        
        return {
            'one_time_users': one_time_users,
            'regular_users': regular_users,
            'power_users': power_users,
            'average_activity_span_days': user_patterns['activity_span'].mean(),
            'user_retention_rate': (len(user_patterns) - one_time_users) / len(user_patterns) * 100
        }
    
    def _calculate_peak_intensity(self, df: pd.DataFrame) -> float:
        """Calculate how intense the peak periods are"""
        hourly_counts = df.groupby('hour')['event_id'].count()
        peak_value = hourly_counts.max()
        average_value = hourly_counts.mean()
        
        return peak_value / average_value if average_value > 0 else 1.0
    
    def _analyze_peak_consistency(self, df: pd.DataFrame) -> Dict[str, float]:
        """Analyze how consistent peak times are across days"""
        
        # Group by date and hour to see daily hourly patterns
        daily_hourly = df.groupby(['date', 'hour'])['event_id'].count().unstack(fill_value=0)
        
        if daily_hourly.empty:
            return {'consistency_score': 0, 'peak_hour_stability': 0}
        
        # Calculate coefficient of variation for each hour across days
        hourly_cv = daily_hourly.std() / daily_hourly.mean()
        hourly_cv = hourly_cv.fillna(0)
        
        # Overall consistency (lower CV = more consistent)
        consistency_score = 1 - (hourly_cv.mean() / 2)  # Normalize roughly to 0-1
        
        # Peak hour stability (how often the same hour is the peak)
        daily_peaks = daily_hourly.idxmax(axis=1)
        peak_mode = daily_peaks.mode()
        peak_stability = (daily_peaks == peak_mode.iloc[0]).mean() if len(peak_mode) > 0 else 0
        
        return {
            'consistency_score': max(0, consistency_score),
            'peak_hour_stability': peak_stability
        }
    
    def _analyze_off_peak_periods(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze off-peak period characteristics"""
        hourly_counts = df.groupby('hour')['event_id'].count()
        
        # Define off-peak as bottom 25% of hours
        off_peak_threshold = hourly_counts.quantile(0.25)
        off_peak_hours = hourly_counts[hourly_counts <= off_peak_threshold].index.tolist()
        
        off_peak_data = df[df['hour'].isin(off_peak_hours)]
        
        return {
            'off_peak_hours': off_peak_hours,
            'off_peak_event_count': len(off_peak_data),
            'off_peak_success_rate': (off_peak_data['access_result'] == 'Granted').mean() * 100 if len(off_peak_data) > 0 else 0,
            'off_peak_unique_users': off_peak_data['person_id'].nunique() if len(off_peak_data) > 0 else 0
        }
    
    def _calculate_growth_acceleration(self, daily_data: pd.Series) -> float:
        """Calculate growth acceleration (second derivative)"""
        if len(daily_data) < 3:
            return 0
        
        # Calculate first differences (velocity)
        velocity = daily_data.diff()
        
        # Calculate second differences (acceleration)
        acceleration = velocity.diff()
        
        return acceleration.mean()
    
    def _calculate_seasonal_strength(self, df: pd.DataFrame) -> float:
        """Calculate strength of seasonal patterns"""
        
        # Day of week variation
        dow_counts = df.groupby('day_of_week')['event_id'].count()
        dow_cv = dow_counts.std() / dow_counts.mean() if dow_counts.mean() > 0 else 0
        
        # Hour of day variation
        hour_counts = df.groupby('hour')['event_id'].count()
        hour_cv = hour_counts.std() / hour_counts.mean() if hour_counts.mean() > 0 else 0
        
        # Combined seasonal strength (higher CV = more seasonal)
        return (dow_cv + hour_cv) / 2
    
    def _summarize_forecast(self, forecast: np.ndarray, historical_avg: float) -> str:
        """Summarize forecast trend"""
        forecast_avg = forecast.mean()
        
        if forecast_avg > historical_avg * 1.1:
            return 'increasing_trend'
        elif forecast_avg < historical_avg * 0.9:
            return 'decreasing_trend'
        else:
            return 'stable_trend'
    
    def _analyze_success_rate_trend(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trends in access success rates"""
        daily_success = df.groupby('date').agg({
            'access_result': lambda x: (x == 'Granted').mean() * 100
        })['access_result']
        
        trend = self._calculate_trend_direction(daily_success.values)
        
        return {
            'current_success_rate': daily_success.iloc[-1] if len(daily_success) > 0 else 0,
            'trend': trend,
            'success_rate_volatility': daily_success.std()
        }
    
    def _calculate_overall_trend_strength(self, df: pd.DataFrame) -> float:
        """Calculate overall trend strength across multiple metrics"""
        
        daily_data = df.groupby('date').agg({
            'event_id': 'count',
            'person_id': 'nunique',
            'access_result': lambda x: (x == 'Granted').mean() * 100
        })
        
        # Calculate trend strength for each metric
        strengths = []
        for column in daily_data.columns:
            trend = self._calculate_trend_direction(daily_data[column].values)
            strengths.append(trend['strength'])
        
        return np.mean(strengths)
    
    def _generate_key_insights(self, df: pd.DataFrame) -> List[str]:
        """Generate key insights from trend analysis"""
        insights = []
        
        # Volume insights
        daily_avg = len(df) / max((df['timestamp'].max() - df['timestamp'].min()).days, 1)
        if daily_avg > 100:
            insights.append(f"High activity system with {daily_avg:.0f} events per day on average")
        
        # Peak time insights
        peak_hour = df.groupby('hour')['event_id'].count().idxmax()
        insights.append(f"Peak activity occurs at {peak_hour}:00")
        
        # Weekend activity
        weekend_pct = len(df[df['is_weekend']]) / len(df) * 100
        if weekend_pct > 20:
            insights.append(f"Significant weekend activity ({weekend_pct:.1f}% of total events)")
        
        # Success rate insight
        success_rate = (df['access_result'] == 'Granted').mean() * 100
        if success_rate < 85:
            insights.append(f"Lower than expected success rate ({success_rate:.1f}%)")
        
        return insights
    
    def _calculate_gini_coefficient(self, values: np.ndarray) -> float:
        """Calculate Gini coefficient for concentration analysis"""
        # Sort values
        sorted_values = np.sort(values)
        n = len(values)
        cumulative = np.cumsum(sorted_values)
        
        # Calculate Gini coefficient
        gini = (2 * np.sum(np.arange(1, n + 1) * sorted_values)) / (n * np.sum(sorted_values)) - (n + 1) / n
        
        return gini
    
    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result structure"""
        return {
            'temporal_trends': {'hourly_distribution': {}, 'daily_distribution': {}},
            'volume_trends': {'daily_volumes': {}, 'volume_statistics': {}},
            'usage_patterns': {'user_patterns': {}, 'door_patterns': {}},
            'peak_analysis': {'peak_hours': [], 'peak_days': []},
            'growth_metrics': {'weekly_growth_rate': 0, 'monthly_growth_rate': 0},
            'seasonal_patterns': {'day_of_week_patterns': {}},
            'forecasting': {'forecast_available': False},
            'trend_summary': {'overall_trend': 'insufficient_data'}
        }

# Factory function
def create_trends_analyzer() -> AccessTrendsAnalyzer:
    """Create access trends analyzer instance"""
    return AccessTrendsAnalyzer()

# Export
__all__ = ['AccessTrendsAnalyzer', 'TrendMetrics', 'create_trends_analyzer']
