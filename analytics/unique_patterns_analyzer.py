#!/usr/bin/env python3
"""
Unique Patterns Analyzer - Modular analytics for unique users and devices
Replace: Add to analytics/ directory
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class UniquePatternAnalyzer:
    """Modular analyzer for unique user and device patterns"""

    def __init__(self):
        self.min_frequency_threshold = 3  # Minimum events to be considered active
        self.anomaly_threshold = 2.5  # Standard deviations for anomaly detection

    def analyze_patterns(
        self, df: pd.DataFrame, metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Main analysis method for unique user/device patterns

        Args:
            df: Combined processed dataframe
            metadata: Database metadata

        Returns:
            Dict containing all pattern analysis results
        """
        if len(df) == 0:
            return {"status": "no_data", "message": "No data available for analysis"}

        # Prepare data
        prepared_df = self._prepare_data(df)

        # Core analyses
        user_patterns = self._analyze_unique_users(prepared_df)
        device_patterns = self._analyze_unique_devices(prepared_df)
        interaction_patterns = self._analyze_user_device_interactions(prepared_df)
        temporal_patterns = self._analyze_temporal_uniqueness(prepared_df)
        access_patterns = self._analyze_access_success_patterns(prepared_df)

        # Advanced analyses
        behavioral_segments = self._segment_unique_behaviors(prepared_df)
        outlier_detection = self._detect_pattern_outliers(prepared_df)
        network_analysis = self._analyze_access_networks(prepared_df)

        return {
            "status": "success",
            "metadata": metadata,
            "analysis_timestamp": datetime.now().isoformat(),
            "data_summary": self._generate_data_summary(prepared_df),
            "user_patterns": user_patterns,
            "device_patterns": device_patterns,
            "interaction_patterns": interaction_patterns,
            "temporal_patterns": temporal_patterns,
            "access_patterns": access_patterns,
            "behavioral_segments": behavioral_segments,
            "outlier_detection": outlier_detection,
            "network_analysis": network_analysis,
            "recommendations": self._generate_recommendations(prepared_df),
        }

    def _prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare data for analysis"""
        prepared_df = df.copy()

        # Ensure timestamp is datetime
        if "timestamp" in prepared_df.columns:
            prepared_df["timestamp"] = pd.to_datetime(
                prepared_df["timestamp"], errors="coerce"
            )
            prepared_df = prepared_df.dropna(subset=["timestamp"])

            # Add time-based features
            prepared_df["hour"] = prepared_df["timestamp"].dt.hour
            prepared_df["day_of_week"] = prepared_df["timestamp"].dt.day_name()
            prepared_df["date"] = prepared_df["timestamp"].dt.date

        # Clean access result
        if "access_result" in prepared_df.columns:
            prepared_df["access_granted"] = (
                prepared_df["access_result"]
                .str.lower()
                .isin(["granted", "success", "true", "1"])
            )

        # Add unique identifiers
        prepared_df["event_id"] = range(len(prepared_df))

        return prepared_df

    def _analyze_unique_users(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze unique user patterns"""
        if "person_id" not in df.columns:
            return {"status": "missing_user_data"}

        user_stats = (
            df.groupby("person_id")
            .agg(
                {
                    "event_id": "count",
                    "door_id": "nunique",
                    "timestamp": ["min", "max"],
                    "access_granted": "mean",
                    "hour": lambda x: x.mode().iloc[0] if len(x) > 0 else 0,
                    "day_of_week": lambda x: (
                        x.mode().iloc[0] if len(x) > 0 else "Unknown"
                    ),
                }
            )
            .round(3)
        )

        user_stats.columns = [
            "total_events",
            "unique_doors",
            "first_access",
            "last_access",
            "success_rate",
            "preferred_hour",
            "preferred_day",
        ]

        # Calculate activity span
        user_stats["activity_span_days"] = (
            user_stats["last_access"] - user_stats["first_access"]
        ).dt.days

        # User classification
        user_classifications = self._classify_users(user_stats)

        # Unique behavior patterns
        unique_behaviors = self._identify_unique_user_behaviors(df, user_stats)

        return {
            "total_unique_users": len(user_stats),
            "active_users": len(
                user_stats[user_stats["total_events"] >= self.min_frequency_threshold]
            ),
            "user_statistics": {
                "mean_events_per_user": user_stats["total_events"].mean(),
                "median_events_per_user": user_stats["total_events"].median(),
                "mean_doors_per_user": user_stats["unique_doors"].mean(),
                "mean_success_rate": user_stats["success_rate"].mean(),
            },
            "user_classifications": user_classifications,
            "unique_behaviors": unique_behaviors,
            "top_users": user_stats.nlargest(10, "total_events").to_dict("index"),
        }

    def _analyze_unique_devices(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze unique device patterns"""
        if "door_id" not in df.columns:
            return {"status": "missing_device_data"}

        device_stats = (
            df.groupby("door_id")
            .agg(
                {
                    "event_id": "count",
                    "person_id": "nunique",
                    "access_granted": "mean",
                    "hour": lambda x: x.mode().iloc[0] if len(x) > 0 else 0,
                    "timestamp": ["min", "max"],
                }
            )
            .round(3)
        )

        device_stats.columns = [
            "total_events",
            "unique_users",
            "success_rate",
            "peak_hour",
            "first_used",
            "last_used",
        ]

        # Device classification
        device_classifications = self._classify_devices(device_stats)

        # Security analysis
        security_analysis = self._analyze_device_security_patterns(df, device_stats)

        # Floor/location analysis if available
        location_analysis = self._analyze_device_locations(df)

        return {
            "total_unique_devices": len(device_stats),
            "active_devices": len(
                device_stats[
                    device_stats["total_events"] >= self.min_frequency_threshold
                ]
            ),
            "device_statistics": {
                "mean_events_per_device": device_stats["total_events"].mean(),
                "median_events_per_device": device_stats["total_events"].median(),
                "mean_users_per_device": device_stats["unique_users"].mean(),
                "mean_success_rate": device_stats["success_rate"].mean(),
            },
            "device_classifications": device_classifications,
            "security_analysis": security_analysis,
            "location_analysis": location_analysis,
            "top_devices": device_stats.nlargest(10, "total_events").to_dict("index"),
        }

    def _analyze_user_device_interactions(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze unique user-device interaction patterns"""
        if not all(col in df.columns for col in ["person_id", "door_id"]):
            return {"status": "missing_interaction_data"}

        # Create interaction matrix
        interaction_matrix = (
            df.groupby(["person_id", "door_id"])
            .agg(
                {
                    "event_id": "count",
                    "access_granted": "mean",
                    "timestamp": ["min", "max"],
                }
            )
            .round(3)
        )

        interaction_matrix.columns = [
            "interaction_count",
            "success_rate",
            "first_interaction",
            "last_interaction",
        ]

        # Find unique interaction patterns
        exclusive_pairs = self._find_exclusive_user_device_pairs(interaction_matrix)
        access_diversity = self._calculate_access_diversity(df)
        behavioral_clusters = self._cluster_interaction_behaviors(interaction_matrix)

        return {
            "total_unique_interactions": len(interaction_matrix),
            "exclusive_relationships": exclusive_pairs,
            "access_diversity": access_diversity,
            "behavioral_clusters": behavioral_clusters,
            "interaction_statistics": {
                "mean_interactions_per_pair": interaction_matrix[
                    "interaction_count"
                ].mean(),
                "median_interactions_per_pair": interaction_matrix[
                    "interaction_count"
                ].median(),
                "highly_active_pairs": len(
                    interaction_matrix[
                        interaction_matrix["interaction_count"]
                        > interaction_matrix["interaction_count"].quantile(0.9)
                    ]
                ),
            },
        }

    def _analyze_temporal_uniqueness(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze temporal patterns for uniqueness"""
        if "timestamp" not in df.columns:
            return {"status": "missing_temporal_data"}

        # Time-based uniqueness patterns
        hourly_patterns = self._analyze_hourly_uniqueness(df)
        daily_patterns = self._analyze_daily_uniqueness(df)
        weekly_patterns = self._analyze_weekly_uniqueness(df)

        # Temporal anomalies
        temporal_anomalies = self._detect_temporal_anomalies(df)

        return {
            "hourly_patterns": hourly_patterns,
            "daily_patterns": daily_patterns,
            "weekly_patterns": weekly_patterns,
            "temporal_anomalies": temporal_anomalies,
        }

    def _analyze_access_success_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze patterns in access success/failure"""
        if "access_granted" not in df.columns:
            return {"status": "missing_access_data"}

        # Success/failure patterns by user
        user_success_patterns = df.groupby("person_id")["access_granted"].agg(
            ["mean", "count", "sum"]
        )
        user_success_patterns["failure_count"] = (
            user_success_patterns["count"] - user_success_patterns["sum"]
        )

        # Success/failure patterns by device
        device_success_patterns = df.groupby("door_id")["access_granted"].agg(
            ["mean", "count", "sum"]
        )
        device_success_patterns["failure_count"] = (
            device_success_patterns["count"] - device_success_patterns["sum"]
        )

        # Identify problematic patterns
        problematic_users = user_success_patterns[
            user_success_patterns["mean"] < 0.5
        ].index.tolist()
        problematic_devices = device_success_patterns[
            device_success_patterns["mean"] < 0.5
        ].index.tolist()

        return {
            "overall_success_rate": df["access_granted"].mean(),
            "users_with_low_success": len(problematic_users),
            "devices_with_low_success": len(problematic_devices),
            "success_distribution": {
                "user_success_stats": user_success_patterns.describe().to_dict(),
                "device_success_stats": device_success_patterns.describe().to_dict(),
            },
            "problematic_entities": {
                "users": problematic_users[:10],  # Top 10 problematic users
                "devices": problematic_devices[:10],  # Top 10 problematic devices
            },
        }

    # Helper methods for advanced analysis
    def _classify_users(self, user_stats: pd.DataFrame) -> Dict[str, List[str]]:
        """Classify users based on behavior patterns"""
        classifications = {
            "power_users": [],
            "regular_users": [],
            "occasional_users": [],
            "single_door_users": [],
            "multi_door_users": [],
            "high_success_users": [],
            "problematic_users": [],
        }

        # Thresholds
        high_activity = user_stats["total_events"].quantile(0.8)
        low_activity = user_stats["total_events"].quantile(0.2)

        for user_id, stats in user_stats.iterrows():
            # Activity-based classification
            if stats["total_events"] >= high_activity:
                classifications["power_users"].append(user_id)
            elif stats["total_events"] >= low_activity:
                classifications["regular_users"].append(user_id)
            else:
                classifications["occasional_users"].append(user_id)

            # Door access pattern
            if stats["unique_doors"] == 1:
                classifications["single_door_users"].append(user_id)
            elif stats["unique_doors"] > 3:
                classifications["multi_door_users"].append(user_id)

            # Success rate classification
            if stats["success_rate"] > 0.95:
                classifications["high_success_users"].append(user_id)
            elif stats["success_rate"] < 0.7:
                classifications["problematic_users"].append(user_id)

        return classifications

    def _classify_devices(self, device_stats: pd.DataFrame) -> Dict[str, List[str]]:
        """Classify devices based on usage patterns"""
        classifications = {
            "high_traffic_devices": [],
            "moderate_traffic_devices": [],
            "low_traffic_devices": [],
            "secure_devices": [],
            "problematic_devices": [],
            "popular_devices": [],
        }

        # Thresholds
        high_traffic = device_stats["total_events"].quantile(0.8)
        low_traffic = device_stats["total_events"].quantile(0.2)

        for device_id, stats in device_stats.iterrows():
            # Traffic-based classification
            if stats["total_events"] >= high_traffic:
                classifications["high_traffic_devices"].append(device_id)
            elif stats["total_events"] >= low_traffic:
                classifications["moderate_traffic_devices"].append(device_id)
            else:
                classifications["low_traffic_devices"].append(device_id)

            # Security-based classification
            if stats["success_rate"] > 0.95:
                classifications["secure_devices"].append(device_id)
            elif stats["success_rate"] < 0.7:
                classifications["problematic_devices"].append(device_id)

            # Popularity (unique users)
            if stats["unique_users"] > device_stats["unique_users"].quantile(0.8):
                classifications["popular_devices"].append(device_id)

        return classifications

    def _generate_data_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate comprehensive data summary"""
        return {
            "total_records": len(df),
            "date_range": {
                "start": (
                    df["timestamp"].min().isoformat()
                    if "timestamp" in df.columns
                    else None
                ),
                "end": (
                    df["timestamp"].max().isoformat()
                    if "timestamp" in df.columns
                    else None
                ),
                "span_days": (
                    (df["timestamp"].max() - df["timestamp"].min()).days
                    if "timestamp" in df.columns
                    else 0
                ),
            },
            "unique_entities": {
                "users": int(df["person_id"].nunique()) if "person_id" in df.columns else 0,
                "devices": int(df["door_id"].nunique()) if "door_id" in df.columns else 0,
                "unique_days": int(df["date"].nunique()) if "date" in df.columns else 0,
            },
            "data_quality": {
                "missing_timestamps": int(
                    df["timestamp"].isna().sum() if "timestamp" in df.columns else 0
                ),
                "missing_users": int(
                    df["person_id"].isna().sum() if "person_id" in df.columns else 0
                ),
                "missing_devices": int(
                    df["door_id"].isna().sum() if "door_id" in df.columns else 0
                ),
            },
        }

    def _generate_recommendations(self, df: pd.DataFrame) -> List[Dict[str, str]]:
        """Generate actionable recommendations based on pattern analysis"""
        recommendations = []

        if "access_granted" in df.columns:
            overall_success_rate = df["access_granted"].mean()
            if overall_success_rate < 0.8:
                recommendations.append(
                    {
                        "category": "Security",
                        "priority": "High",
                        "recommendation": f"Overall access success rate is {overall_success_rate:.1%}. Investigate failed access patterns.",
                        "action": "Review user permissions and device configurations",
                    }
                )

        if "person_id" in df.columns:
            unique_users = df["person_id"].nunique()
            total_events = len(df)
            if total_events / unique_users > 100:  # Very high activity per user
                recommendations.append(
                    {
                        "category": "Usage",
                        "priority": "Medium",
                        "recommendation": f"High activity ratio ({total_events/unique_users:.1f} events per user). Consider usage optimization.",
                        "action": "Analyze user behavior patterns for efficiency improvements",
                    }
                )

        return recommendations

    # Placeholder methods for advanced analyses (implement as needed)
    def _identify_unique_user_behaviors(
        self, df: pd.DataFrame, user_stats: pd.DataFrame
    ) -> Dict[str, Any]:
        """Identify unique behavioral patterns among users"""
        return {"status": "analysis_placeholder"}

    def _analyze_device_security_patterns(
        self, df: pd.DataFrame, device_stats: pd.DataFrame
    ) -> Dict[str, Any]:
        """Analyze security-related device patterns"""
        return {"status": "analysis_placeholder"}

    def _analyze_device_locations(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze device location patterns if floor/location data available"""
        return {"status": "analysis_placeholder"}

    def _find_exclusive_user_device_pairs(
        self, interaction_matrix: pd.DataFrame
    ) -> Dict[str, Any]:
        """Find exclusive user-device relationships"""
        return {"status": "analysis_placeholder"}

    def _calculate_access_diversity(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate diversity metrics for access patterns"""
        return {"status": "analysis_placeholder"}

    def _cluster_interaction_behaviors(
        self, interaction_matrix: pd.DataFrame
    ) -> Dict[str, Any]:
        """Cluster similar interaction behaviors"""
        return {"status": "analysis_placeholder"}

    def _analyze_hourly_uniqueness(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze unique patterns by hour"""
        return {"status": "analysis_placeholder"}

    def _analyze_daily_uniqueness(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze unique patterns by day"""
        return {"status": "analysis_placeholder"}

    def _analyze_weekly_uniqueness(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze unique patterns by week"""
        return {"status": "analysis_placeholder"}

    def _detect_temporal_anomalies(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect temporal anomalies in access patterns"""
        return {"status": "analysis_placeholder"}

    def _segment_unique_behaviors(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Segment behaviors into unique categories"""
        return {"status": "analysis_placeholder"}

    def _detect_pattern_outliers(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect outliers in access patterns"""
        return {"status": "analysis_placeholder"}

    def _analyze_access_networks(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze network relationships in access patterns"""
        return {"status": "analysis_placeholder"}
