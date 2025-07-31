#!/usr/bin/env python3
"""
Run actual analytics on Enhanced Security Demo data
"""

import asyncio
import json
import sys
from pathlib import Path

from config.app_config import UploadConfig

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def run_real_analytics():
    try:
        print("=== RUNNING REAL ANALYTICS ON ACCESS CONTROL DATA ===")

        import pandas as pd

        from yosai_intel_dashboard.src.services.analytics_service import AnalyticsService

        # Load the Enhanced Security Demo data
        parquet_path = (
            Path(UploadConfig().folder) / "Enhanced_Security_Demo.csv.parquet"
        )
        df = pd.read_parquet(parquet_path)

        print(f"Data loaded: {len(df)} access events")
        print(f"Columns: {list(df.columns)}")
        print(f"Date range: {df['Event Time'].min()} to {df['Event Time'].max()}")
        print(f"Unique employees: {df['Employee Code'].nunique()}")
        print(f"Unique doors: {df['Door Location'].nunique()}")

        # Initialize analytics service
        analytics = AnalyticsService()

        # Test 1: Dashboard Summary
        print("\n--- Dashboard Summary ---")
        try:
            summary = analytics.get_dashboard_summary()
            print(f"Dashboard summary: {summary}")
        except Exception as e:
            print(f"Dashboard summary failed: {e}")

        # Test 2: Access Pattern Analysis
        print("\n--- Access Pattern Analysis ---")
        try:
            access_patterns = analytics.analyze_access_patterns(days=30)
            print(f"Access patterns: {access_patterns}")
        except Exception as e:
            print(f"Access patterns failed: {e}")

        # Test 3: Uploaded Data Analytics
        print("\n--- Uploaded Data Analytics ---")
        try:
            uploaded_analytics = analytics.get_analytics_from_uploaded_data()
            print(f"Uploaded analytics: {uploaded_analytics}")
        except Exception as e:
            print(f"Uploaded analytics failed: {e}")

        # Test 4: Anomaly Detection
        print("\n--- Anomaly Detection ---")
        try:
            anomalies = analytics.detect_anomalies(df)
            print(
                f"Anomalies detected: {len(anomalies) if isinstance(anomalies, list) else anomalies}"
            )
        except Exception as e:
            print(f"Anomaly detection failed: {e}")

        print("\n=== ANALYTICS TESTING COMPLETE ===")

    except Exception as e:
        print(f"Analytics testing failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_real_analytics())
