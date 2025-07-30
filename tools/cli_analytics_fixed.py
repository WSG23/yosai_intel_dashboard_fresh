#!/usr/bin/env python3
"""
Test Analytics with callback fix applied
"""

import asyncio
import json
import sys
import logging
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

# Apply callback patch first
try:
    from core.callbacks import UnifiedCallbackManager as CallbackManager

    if hasattr(CallbackManager, "handle_register") and not hasattr(
        CallbackManager, "register_handler"
    ):
        CallbackManager.register_handler = CallbackManager.handle_register
        logger.info("✅ Callback patch applied")
except Exception as e:
    logger.warning("⚠️  Callback patch failed: %s", e)


async def test_analytics_with_fix():
    try:
        logger.info("=== TESTING ANALYTICS WITH CALLBACK FIX ===")

        import pandas as pd

        from services.analytics_service import AnalyticsService

        # Load the Enhanced Security Demo data
        parquet_path = Path("temp/uploaded_data/Enhanced_Security_Demo.csv.parquet")
        df = pd.read_parquet(parquet_path)

        logger.info("Data loaded: %d access events", len(df))
        logger.info("Unique employees: %d", df['Employee Code'].nunique())
        logger.info("Unique doors: %d", df['Door Location'].nunique())

        # Initialize analytics service (should work without callback errors now)
        logger.info("\n--- Initializing AnalyticsService ---")
        try:
            analytics = AnalyticsService()
            logger.info("✅ AnalyticsService initialized successfully!")

            # Test health check
            health = analytics.health_check()
            logger.info("Health check: %s", health)

        except Exception as e:
            logger.error("❌ AnalyticsService initialization failed: %s", e)
            return {"success": False, "error": str(e)}

        result = {"success": True, "tests": {}}

        # Test 1: Dashboard Summary
        logger.info("\n--- Dashboard Summary ---")
        try:
            summary = analytics.get_dashboard_summary()
            result["tests"]["dashboard_summary"] = {"success": True, "result": summary}
            logger.info("✅ Dashboard summary: %s", summary.get('status', 'unknown'))
        except Exception as e:
            result["tests"]["dashboard_summary"] = {"success": False, "error": str(e)}
            logger.error("❌ Dashboard summary failed: %s", e)

        # Test 2: Access Pattern Analysis
        logger.info("\n--- Access Pattern Analysis ---")
        try:
            access_patterns = analytics.analyze_access_patterns(
                days=1
            )  # Use 1 day since our data is from one day
            result["tests"]["access_patterns"] = {
                "success": True,
                "result": access_patterns,
            }
            logger.info(
                "✅ Access patterns found: %d",
                len(access_patterns.get('patterns', [])),
            )
        except Exception as e:
            result["tests"]["access_patterns"] = {"success": False, "error": str(e)}
            logger.error("❌ Access patterns failed: %s", e)

        # Test 3: Anomaly Detection
        logger.info("\n--- Anomaly Detection ---")
        try:
            anomalies = analytics.detect_anomalies(df)
            result["tests"]["anomaly_detection"] = {
                "success": True,
                "result": anomalies,
            }
            logger.info(
                "✅ Anomalies detected: %s",
                len(anomalies) if isinstance(anomalies, list) else "N/A",
            )
        except Exception as e:
            result["tests"]["anomaly_detection"] = {"success": False, "error": str(e)}
            logger.error("❌ Anomaly detection failed: %s", e)

        # Test 4: Data Processing
        logger.info("\n--- Data Processing ---")
        try:
            processed = analytics.clean_uploaded_dataframe(df)
            result["tests"]["data_processing"] = {
                "success": True,
                "rows": len(processed),
            }
            logger.info("✅ Data processed: %d rows", len(processed))
        except Exception as e:
            result["tests"]["data_processing"] = {"success": False, "error": str(e)}
            logger.error("❌ Data processing failed: %s", e)

        logger.info("\n=== ANALYTICS TESTING WITH FIX COMPLETE ===")
        return result

    except Exception as e:
        logger.exception("Analytics testing failed: %s", e)
        return {"success": False, "error": str(e)}


def main():
    result = asyncio.run(test_analytics_with_fix())
    logger.info("\n" + "=" * 50)
    logger.info("FINAL RESULTS:")
    logger.info(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
