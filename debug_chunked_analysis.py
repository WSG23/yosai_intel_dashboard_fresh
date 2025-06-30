#!/usr/bin/env python3
"""
Debug script to test chunked analysis with your dataset.
Run this to verify the fix works.
"""

import pandas as pd
import logging
from services.analytics_service import AnalyticsService

# Setup logging to see all debug info
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_chunked_analysis():
    """Test chunked analysis with sample data."""

    # Create test dataset with 2500 rows (matches your scenario)
    logger.info("🔧 Creating test dataset with 2500 rows...")
    test_data = []
    for i in range(2500):
        test_data.append({
            'person_id': f'USER_{i % 150}',  # 150 unique users
            'door_id': f'DOOR_{i % 75}',     # 75 unique doors  
            'access_result': 'Granted' if i % 4 != 0 else 'Denied',
            'timestamp': f'2024-01-{(i % 30) + 1:02d} {(i % 24):02d}:{(i % 60):02d}:00'
        })

    df = pd.DataFrame(test_data)
    logger.info(f"✅ Created test dataset: {len(df):,} rows")

    # Test analytics service
    service = AnalyticsService()

    # Run chunked analysis
    logger.info("🚀 Starting chunked analysis test...")
    result = service.analyze_with_chunking(df, ["security", "trends", "anomaly", "behavior"])

    # Verify results
    logger.info("📊 ANALYSIS RESULTS:")
    logger.info(f"   Total events: {result.get('total_events', 0):,}")
    logger.info(f"   Unique users: {result.get('unique_users', 0):,}")
    logger.info(f"   Unique doors: {result.get('unique_doors', 0):,}")
    logger.info(f"   Rows processed: {result.get('rows_processed', 0):,}")

    # Check processing summary
    summary = result.get('processing_summary', {})
    logger.info("🔍 PROCESSING SUMMARY:")
    for key, value in summary.items():
        logger.info(f"   {key}: {value}")

    # Verification
    expected_rows = 2500
    actual_rows = result.get('rows_processed', 0)

    if actual_rows == expected_rows:
        logger.info(f"🎉 SUCCESS: Processed ALL {actual_rows:,} rows correctly!")
        return True
    else:
        logger.error(f"❌ FAILURE: Expected {expected_rows:,} rows, got {actual_rows:,}")
        return False


if __name__ == "__main__":
    success = test_chunked_analysis()
    exit(0 if success else 1)
