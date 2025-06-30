#!/usr/bin/env python3
"""
Quick test to verify the datetime fix works
Run this after applying the datetime parsing fixes
"""

import sys
import pandas as pd
from datetime import datetime, timedelta
import random

# Create test data with proper timestamp format
def create_test_data(rows=2500):
    data = []
    base_date = datetime(2024, 1, 1)
    
    for i in range(rows):
        data.append({
            'person_id': f'USER_{(i % 150) + 1:03d}',
            'door_id': f'DOOR_{(i % 25) + 1:02d}',
            'access_result': random.choice(['Granted', 'Granted', 'Granted', 'Denied']),
            'timestamp': (base_date + timedelta(minutes=i)).isoformat(),
            'badge_id': f'BADGE_{i % 200:04d}'
        })
    
    return pd.DataFrame(data)

# Test the datetime parsing fix
def test_datetime_parsing():
    print("🧪 Testing datetime parsing fix...")
    
    df = create_test_data(100)  # Small test
    print(f"Created test data: {len(df)} rows")
    
    # Test the ensure_datetime_columns function
    from services.analytics_service import ensure_datetime_columns
    
    print(f"Before: timestamp dtype = {df['timestamp'].dtype}")
    df_fixed = ensure_datetime_columns(df)
    print(f"After: timestamp dtype = {df_fixed['timestamp'].dtype}")
    
    # Test datetime operations
    if hasattr(df_fixed['timestamp'].dt, 'date'):
        dates = df_fixed['timestamp'].dt.date
        print(f"✅ Successfully extracted dates: {dates.min()} to {dates.max()}")
        return True
    else:
        print("❌ Datetime conversion failed")
        return False

# Test analytics service with the fix
def test_analytics_service():
    print("🔬 Testing AnalyticsService...")
    
    try:
        from services.analytics_service import AnalyticsService
        
        df = create_test_data(100)
        service = AnalyticsService()
        
        # This should now work without the datetime error
        result = service.analyze_with_chunking(df, ["basic"])
        
        rows_processed = result.get("processing_summary", {}).get("rows_processed", 0)
        print(f"✅ Analytics completed: {rows_processed} rows processed")
        return rows_processed == len(df)
        
    except Exception as e:
        print(f"❌ Analytics test failed: {e}")
        return False

def main():
    print("🚀 QUICK DATETIME FIX TEST")
    print("=" * 40)
    
    # Test 1: Datetime parsing
    datetime_ok = test_datetime_parsing()
    
    print("\n" + "=" * 40)
    
    # Test 2: Analytics service
    analytics_ok = test_analytics_service()
    
    print("\n" + "=" * 40)
    print("📊 RESULTS:")
    print(f"  Datetime parsing: {'✅ PASS' if datetime_ok else '❌ FAIL'}")
    print(f"  Analytics service: {'✅ PASS' if analytics_ok else '❌ FAIL'}")
    
    if datetime_ok and analytics_ok:
        print("\n🎉 ALL TESTS PASSED! The datetime fix is working.")
        print("Your system should now process complete datasets correctly.")
    else:
        print("\n⚠️ Some tests failed. Check the error messages above.")
    
    return datetime_ok and analytics_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)