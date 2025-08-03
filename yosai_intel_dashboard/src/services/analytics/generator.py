from __future__ import annotations

"""Analytics generation helpers packaged as a service."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict

import numpy as np
import pandas as pd

from yosai_intel_dashboard.src.core.cache_manager import (
    CacheConfig,
    InMemoryCacheManager,
    cache_with_lock,
)
from yosai_intel_dashboard.src.infrastructure.config import get_cache_config

from .approximation import approximate_unique_count

cfg = get_cache_config()
_cache_manager = InMemoryCacheManager(CacheConfig(timeout_seconds=cfg.ttl))

logger = logging.getLogger(__name__)


class AnalyticsGenerator:
    """Generate summaries and sample analytics."""

    @cache_with_lock(_cache_manager, ttl=600)
    def summarize_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        total_events = len(df)
        active_users = (
            approximate_unique_count(df["person_id"])
            if "person_id" in df.columns
            else 0
        )
        active_doors = (
            approximate_unique_count(df["door_id"]) if "door_id" in df.columns else 0
        )

        date_range = {"start": "Unknown", "end": "Unknown"}
        if "timestamp" in df.columns:
            valid_ts = df["timestamp"].dropna()
            if not valid_ts.empty:
                date_range = {
                    "start": str(valid_ts.min().date()),
                    "end": str(valid_ts.max().date()),
                }

        access_patterns = {}
        if "access_result" in df.columns:
            access_patterns = df["access_result"].value_counts().to_dict()

        top_users = []
        if "person_id" in df.columns:
            user_counts = df["person_id"].value_counts().head(10)
            top_users = [
                {"user_id": uid, "count": int(cnt)} for uid, cnt in user_counts.items()
            ]

        top_doors = []
        if "door_id" in df.columns:
            door_counts = df["door_id"].value_counts().head(10)
            top_doors = [
                {"door_id": did, "count": int(cnt)} for did, cnt in door_counts.items()
            ]

        return {
            "total_events": total_events,
            "active_users": active_users,
            "active_doors": active_doors,
            "unique_users": active_users,
            "unique_doors": active_doors,
            "data_source": "uploaded",
            "date_range": date_range,
            "access_patterns": access_patterns,
            "top_users": top_users,
            "top_doors": top_doors,
        }

    @cache_with_lock(_cache_manager, ttl=3600)
    def create_sample_data(self, n_events: int = 1000) -> pd.DataFrame:
        np.random.seed(42)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        timestamps = [
            start_date
            + timedelta(
                days=np.random.randint(0, 30),
                hours=np.random.randint(0, 24),
                minutes=np.random.randint(0, 60),
            )
            for _ in range(n_events)
        ]
        users = [f"USER{i:04d}" for i in range(1, 51)]
        doors = [f"DOOR{i:03d}" for i in range(1, 6)]
        data = {
            "event_id": [f"EVT{i:06d}" for i in range(n_events)],
            "timestamp": timestamps,
            "person_id": np.random.choice(users, n_events),
            "door_id": np.random.choice(doors, n_events),
            "access_result": np.random.choice(
                ["Granted", "Denied"], n_events, p=[0.85, 0.15]
            ),
            "badge_status": np.random.choice(
                ["Valid", "Invalid", "Expired"], n_events, p=[0.9, 0.08, 0.02]
            ),
            "device_status": np.random.choice(
                ["normal", "maintenance"], n_events, p=[0.95, 0.05]
            ),
        }
        df = pd.DataFrame(data).sort_values("timestamp").reset_index(drop=True)
        return df

    @cache_with_lock(_cache_manager, ttl=600)
    def analyze_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        if df.empty:
            return {"total_events": 0}

        df["timestamp"] = pd.to_datetime(df["timestamp"])
        total_events = len(df)
        unique_users = approximate_unique_count(df["person_id"])
        unique_doors = approximate_unique_count(df["door_id"])

        access_counts = df["access_result"].value_counts()
        granted = access_counts.get("Granted", 0)
        denied = access_counts.get("Denied", 0)
        success_rate = (granted / total_events) * 100 if total_events else 0

        date_range = {
            "start": df["timestamp"].min().isoformat(),
            "end": df["timestamp"].max().isoformat(),
            "days": (df["timestamp"].max() - df["timestamp"].min()).days + 1,
        }
        hourly_dist = df["timestamp"].dt.hour.value_counts().sort_index().to_dict()
        daily_dist = df["timestamp"].dt.day_name().value_counts().to_dict()

        return {
            "total_events": total_events,
            "unique_users": unique_users,
            "unique_doors": unique_doors,
            "success_rate": round(success_rate, 2),
            "granted_events": int(granted),
            "denied_events": int(denied),
            "date_range": date_range,
            "hourly_distribution": hourly_dist,
            "daily_distribution": daily_dist,
        }

    @cache_with_lock(_cache_manager, ttl=600)
    def generate_basic_analytics(self, df: pd.DataFrame) -> Dict[str, Any]:
        try:
            analytics: Dict[str, Any] = {
                "status": "success",
                "total_events": len(df),
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "summary": {},
                "timestamp": datetime.now().isoformat(),
            }
            for col in df.columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    analytics["summary"][col] = {
                        "type": "numeric",
                        "mean": float(df[col].mean()),
                        "min": float(df[col].min()),
                        "max": float(df[col].max()),
                        "null_count": int(df[col].isnull().sum()),
                    }
                else:
                    counts = df[col].value_counts().head(10)
                    analytics["summary"][col] = {
                        "type": "categorical",
                        "unique_values": approximate_unique_count(df[col]),
                        "top_values": {str(k): int(v) for k, v in counts.items()},
                        "null_count": int(df[col].isnull().sum()),
                    }
            return analytics
        except Exception as exc:  # pragma: no cover - best effort
            logger.error("Error generating basic analytics: %s", exc)
            return {"status": "error", "message": str(exc)}

    @cache_with_lock(_cache_manager, ttl=3600)
    def generate_sample_analytics(self) -> Dict[str, Any]:
        df = self.create_sample_data()
        basic = self.generate_basic_analytics(df)
        basic.update(self.analyze_dataframe(df))
        return basic


__all__ = ["AnalyticsGenerator"]
