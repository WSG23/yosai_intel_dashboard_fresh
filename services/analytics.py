"""Simplified analytics service"""
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from database.connection import DatabaseConnection
from core.exceptions import ServiceUnavailableError


class EventAnalyzer:
    """Handles event data analysis"""
    
    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection
    
    def get_summary_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get basic summary statistics"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            query = """
                SELECT event_type, status, COUNT(*) as count
                FROM access_events 
                WHERE timestamp >= ? AND timestamp <= ?
                GROUP BY event_type, status
            """
            
            df = self.db.execute_query(query, (start_date, end_date))
            
            if df.empty:
                return self._empty_stats()
            
            return {
                'total_events': df['count'].sum(),
                'success_rate': self._calculate_success_rate(df),
                'event_breakdown': df.to_dict('records'),
                'period_days': days
            }
            
        except Exception as e:
            raise ServiceUnavailableError(f"Failed to get summary stats: {e}")
    
    def get_hourly_patterns(self, days: int = 7) -> Dict[str, Any]:
        """Analyze hourly access patterns"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            query = """
                SELECT 
                    strftime('%H', timestamp) as hour,
                    COUNT(*) as event_count
                FROM access_events 
                WHERE timestamp >= ? AND timestamp <= ?
                GROUP BY strftime('%H', timestamp)
                ORDER BY hour
            """
            
            df = self.db.execute_query(query, (start_date, end_date))
            
            if df.empty:
                return {'hourly_data': [], 'peak_hour': None}
            
            hourly_data = df.to_dict('records')
            peak_hour = df.loc[df['event_count'].idxmax(), 'hour']
            
            return {
                'hourly_data': hourly_data,
                'peak_hour': int(peak_hour),
                'total_hours_analyzed': len(hourly_data)
            }
            
        except Exception as e:
            raise ServiceUnavailableError(f"Failed to analyze hourly patterns: {e}")
    
    def detect_anomalies(self, threshold_multiplier: float = 2.0) -> List[Dict[str, Any]]:
        """Simple anomaly detection based on statistical outliers"""
        try:
            # Get recent event counts by hour
            query = """
                SELECT 
                    datetime(timestamp) as event_time,
                    COUNT(*) as event_count
                FROM access_events 
                WHERE timestamp >= datetime('now', '-24 hours')
                GROUP BY datetime(strftime('%Y-%m-%d %H:00:00', timestamp))
                ORDER BY event_time
            """
            
            df = self.db.execute_query(query)
            
            if len(df) < 3:  # Need minimum data for anomaly detection
                return []
            
            # Calculate statistical thresholds
            mean_count = df['event_count'].mean()
            std_count = df['event_count'].std()
            threshold = mean_count + (threshold_multiplier * std_count)
            
            # Find anomalies
            anomalies = df[df['event_count'] > threshold]
            
            return [
                {
                    'time': row['event_time'],
                    'event_count': row['event_count'],
                    'severity': 'high' if row['event_count'] > threshold * 1.5 else 'medium',
                    'description': f"Unusual activity: {row['event_count']} events (normal: ~{mean_count:.1f})"
                }
                for _, row in anomalies.iterrows()
            ]
            
        except Exception as e:
            raise ServiceUnavailableError(f"Failed to detect anomalies: {e}")
    
    def _calculate_success_rate(self, df: pd.DataFrame) -> float:
        """Calculate overall success rate"""
        total_events = df['count'].sum()
        if total_events == 0:
            return 0.0
        
        success_events = df[df['status'] == 'success']['count'].sum()
        return round((success_events / total_events) * 100, 2)
    
    def _empty_stats(self) -> Dict[str, Any]:
        """Return empty statistics structure"""
        return {
            'total_events': 0,
            'success_rate': 0.0,
            'event_breakdown': [],
            'period_days': 0
        }


class LocationAnalyzer:
    """Handles location-based analysis"""
    
    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection
    
    def get_location_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get statistics by location"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            query = """
                SELECT 
                    location,
                    COUNT(*) as total_events,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful_events
                FROM access_events 
                WHERE timestamp >= ? AND timestamp <= ?
                GROUP BY location
                ORDER BY total_events DESC
            """
            
            df = self.db.execute_query(query, (start_date, end_date))
            
            if df.empty:
                return {'locations': [], 'busiest_location': None}
            
            # Calculate success rates
            df['success_rate'] = (df['successful_events'] / df['total_events'] * 100).round(2)
            
            locations = df.to_dict('records')
            busiest_location = df.iloc[0]['location'] if len(df) > 0 else None
            
            return {
                'locations': locations,
                'busiest_location': busiest_location,
                'total_locations': len(locations)
            }
            
        except Exception as e:
            raise ServiceUnavailableError(f"Failed to analyze locations: {e}")


class AnalyticsService:
    """Main analytics service combining all analyzers"""
    
    def __init__(self, db_connection: DatabaseConnection):
        self.event_analyzer = EventAnalyzer(db_connection)
        self.location_analyzer = LocationAnalyzer(db_connection)
    
    def get_dashboard_data(self, days: int = 7) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        try:
            return {
                'summary': self.event_analyzer.get_summary_stats(days),
                'hourly_patterns': self.event_analyzer.get_hourly_patterns(days),
                'location_stats': self.location_analyzer.get_location_stats(days),
                'anomalies': self.event_analyzer.detect_anomalies(),
                'generated_at': datetime.now().isoformat()
            }
        except Exception as e:
            raise ServiceUnavailableError(f"Failed to generate dashboard data: {e}")
    
    def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        try:
            # Simple query to verify database connectivity
            stats = self.event_analyzer.get_summary_stats(1)
            return {
                'status': 'healthy',
                'database_responsive': True,
                'last_check': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'database_responsive': False,
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }


# Factory function for dependency injection
def create_analytics_service(db_connection: DatabaseConnection) -> AnalyticsService:
    """Create analytics service instance"""
    return AnalyticsService(db_connection)
