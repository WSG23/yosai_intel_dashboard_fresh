#!/usr/bin/env python3
"""
Test Analytics with callback fix applied
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Apply callback patch first
try:
    from core.truly_unified_callbacks import TrulyUnifiedCallbacks as CallbackManager

    if hasattr(CallbackManager, "handle_register") and not hasattr(
        CallbackManager, "register_handler"
    ):
        CallbackManager.register_handler = CallbackManager.handle_register
        print("✅ Callback patch applied")
except Exception as e:
    print(f"⚠️  Callback patch failed: {e}")


async def test_analytics_with_fix():
    try:
        print("=== TESTING ANALYTICS WITH CALLBACK FIX ===")

        import pandas as pd

        from services.analytics_service import AnalyticsService

        # Load the Enhanced Security Demo data
        parquet_path = Path("temp/uploaded_data/Enhanced_Security_Demo.csv.parquet")
        df = pd.read_parquet(parquet_path)

        print(f"Data loaded: {len(df)} access events")
        print(f"Unique employees: {df['Employee Code'].nunique()}")
        print(f"Unique doors: {df['Door Location'].nunique()}")

        # Initialize analytics service (should work without callback errors now)
        print("\n--- Initializing AnalyticsService ---")
        try:
            analytics = AnalyticsService()
            print("✅ AnalyticsService initialized successfully!")

            # Test health check
            health = analytics.health_check()
            print(f"Health check: {health}")

        except Exception as e:
            print(f"❌ AnalyticsService initialization failed: {e}")
            return {"success": False, "error": str(e)}

        result = {"success": True, "tests": {}}

        # Test 1: Dashboard Summary
        print("\n--- Dashboard Summary ---")
        try:
            summary = analytics.get_dashboard_summary()
            result["tests"]["dashboard_summary"] = {"success": True, "result": summary}
            print(f"✅ Dashboard summary: {summary.get('status', 'unknown')}")
        except Exception as e:
            result["tests"]["dashboard_summary"] = {"success": False, "error": str(e)}
            print(f"❌ Dashboard summary failed: {e}")

        # Test 2: Access Pattern Analysis
        print("\n--- Access Pattern Analysis ---")
        try:
            access_patterns = analytics.analyze_access_patterns(
                days=1
            )  # Use 1 day since our data is from one day
            result["tests"]["access_patterns"] = {
                "success": True,
                "result": access_patterns,
            }
            print(
                f"✅ Access patterns found: {len(access_patterns.get('patterns', []))}"
            )
        except Exception as e:
            result["tests"]["access_patterns"] = {"success": False, "error": str(e)}
            print(f"❌ Access patterns failed: {e}")

        # Test 3: Anomaly Detection
        print("\n--- Anomaly Detection ---")
        try:
            anomalies = analytics.detect_anomalies(df)
            result["tests"]["anomaly_detection"] = {
                "success": True,
                "result": anomalies,
            }
            print(
                f"✅ Anomalies detected: {len(anomalies) if isinstance(anomalies, list) else 'N/A'}"
            )
        except Exception as e:
            result["tests"]["anomaly_detection"] = {"success": False, "error": str(e)}
            print(f"❌ Anomaly detection failed: {e}")

        # Test 4: Data Processing
        print("\n--- Data Processing ---")
        try:
            processed = analytics.clean_uploaded_dataframe(df)
            result["tests"]["data_processing"] = {
                "success": True,
                "rows": len(processed),
            }
            print(f"✅ Data processed: {len(processed)} rows")
        except Exception as e:
            result["tests"]["data_processing"] = {"success": False, "error": str(e)}
            print(f"❌ Data processing failed: {e}")

        print("\n=== ANALYTICS TESTING WITH FIX COMPLETE ===")
        return result

    except Exception as e:
        print(f"Analytics testing failed: {e}")
        import traceback

        traceback.print_exc()
        return {"success": False, "error": str(e)}


def main():
    logging.basicConfig(level=logging.INFO)
    result = asyncio.run(test_analytics_with_fix())
    print("\n" + "=" * 50)
    print("FINAL RESULTS:")
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
