#!/usr/bin/env python3
"""
UNIQUE PATTERNS SPECIFIC DEBUG
Test the exact code path that's causing 150 rows in unique patterns analysis
"""

import logging
import sys
import pandas as pd

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_unique_patterns_specific():
    """Test the exact unique patterns analysis that's showing 150"""
    
    print(" UNIQUE PATTERNS ANALYSIS DEBUG")
    print("=" * 60)
    
    # Step 1: Setup test data (same as before)
    print(" STEP 1: Setting up test data")
    test_data = []
    for i in range(2500):
        test_data.append({
            'person_id': f'USER_{i % 200}',
            'door_id': f'DOOR_{i % 100}',
            'access_result': 'Granted' if i % 3 != 0 else 'Denied',
            'timestamp': f'2024-01-{(i % 30) + 1:02d} {(i % 24):02d}:{(i % 60):02d}:00'
        })
    
    original_df = pd.DataFrame(test_data)
    
    # Add to upload store
    try:
        from utils.upload_store import uploaded_data_store
        uploaded_data_store.clear_all()
        uploaded_data_store.add_file("debug_unique_patterns.csv", original_df)
        print(f" Added {len(original_df):,} rows to upload store")
    except Exception as e:
        print(f" Error setting up upload store: {e}")
        return
    print()
    
    # Step 2: Test get_uploaded_data directly
    print(" STEP 2: Testing get_uploaded_data()")
    try:
        from pages.file_upload import get_uploaded_data
        uploaded_data = get_uploaded_data()
        
        if uploaded_data:
            print(f"    Found {len(uploaded_data)} files:")
            for filename, df in uploaded_data.items():
                print(f"     {filename}: {len(df):,} rows")
                
                # Check if any file has exactly 150 rows
                if len(df) == 150:
                    print(f"      FOUND 150 ROW LIMIT in uploaded data!")
        else:
            print("    No uploaded data found")
            return
    except Exception as e:
        print(f" Error testing get_uploaded_data: {e}")
        return
    print()
    
    # Step 3: Test analytics service creation
    print("  STEP 3: Testing AnalyticsService creation")
    try:
        from services import AnalyticsService
        service = AnalyticsService()
        print("    AnalyticsService created successfully")
    except Exception as e:
        print(f" Error creating AnalyticsService: {e}")
        return
    print()
    
    # Step 4: Test clean_uploaded_dataframe method
    print(" STEP 4: Testing clean_uploaded_dataframe")
    try:
        filename, df = next(iter(uploaded_data.items()))
        print(f"   Original dataframe: {len(df):,} rows")
        
        cleaned_df = service.clean_uploaded_dataframe(df)
        print(f"   Cleaned dataframe: {len(cleaned_df):,} rows")
        
        if len(cleaned_df) == 150:
            print(f"    FOUND 150 ROW LIMIT in clean_uploaded_dataframe!")
        elif len(cleaned_df) != len(df):
            print(f"     Row count changed during cleaning: {len(df):,} → {len(cleaned_df):,}")
            
    except Exception as e:
        print(f" Error testing clean_uploaded_dataframe: {e}")
        import traceback
        traceback.print_exc()
    print()
    
    # Step 5: Test the EXACT get_unique_patterns_analysis method
    print(" STEP 5: Testing get_unique_patterns_analysis() - THE ACTUAL METHOD")
    try:
        print("   Calling service.get_unique_patterns_analysis()...")
        result = service.get_unique_patterns_analysis()
        
        print(f"   Status: {result.get('status', 'unknown')}")
        
        if 'data_summary' in result:
            total_records = result['data_summary'].get('total_records', 0)
            print(f"   Total records: {total_records:,}")
            
            # THIS IS THE KEY CHECK
            if total_records == 150:
                print(f"    FOUND THE 150 ROW LIMIT IN get_unique_patterns_analysis()!")
                print(f"   This is exactly what shows in the UI!")
            elif total_records == 2500:
                print(f"    Method correctly returns 2,500 rows")
            else:
                print(f"     Unexpected count: {total_records}")
                
            # Check other fields
            if 'unique_entities' in result['data_summary']:
                users = result['data_summary']['unique_entities'].get('users', 0)
                devices = result['data_summary']['unique_entities'].get('devices', 0)
                print(f"   Unique users: {users:,}")
                print(f"   Unique devices: {devices:,}")
        else:
            print("    No data_summary in result")
            print(f"   Result keys: {list(result.keys())}")
            
    except Exception as e:
        print(f" Error testing get_unique_patterns_analysis: {e}")
        import traceback
        traceback.print_exc()
    print()
    
    # Step 6: Test each part of the unique patterns method manually
    print(" STEP 6: Manual step-by-step test of unique patterns logic")
    try:
        print("   6a. Getting uploaded data...")
        from pages.file_upload import get_uploaded_data
        uploaded_data = get_uploaded_data()
        print(f"      Found {len(uploaded_data)} files")
        
        print("   6b. Processing first file...")
        filename, df = next(iter(uploaded_data.items()))
        print(f"      Original: {len(df):,} rows")
        
        print("   6c. Cleaning dataframe...")
        from utils.mapping_helpers import map_and_clean
        cleaned_df = map_and_clean(df)
        print(f"      After map_and_clean: {len(cleaned_df):,} rows")
        
        if len(cleaned_df) == 150:
            print(f"       FOUND 150 ROW LIMIT in map_and_clean!")
        
        print("   6d. Calculating statistics...")
        total_records = len(cleaned_df)
        unique_users = cleaned_df['person_id'].nunique() if 'person_id' in cleaned_df.columns else 0
        unique_devices = cleaned_df['door_id'].nunique() if 'door_id' in cleaned_df.columns else 0
        
        print(f"      Final statistics:")
        print(f"        Total records: {total_records:,}")
        print(f"        Unique users: {unique_users:,}")
        print(f"        Unique devices: {unique_devices:,}")
        
        if total_records == 150:
            print(f"       CONFIRMED: The issue is in the data processing pipeline!")
            
    except Exception as e:
        print(f" Error in manual testing: {e}")
        import traceback
        traceback.print_exc()
    print()
    
    # Step 7: Check if there's any data sampling/limiting
    print(" STEP 7: Check for data sampling or limiting")
    try:
        # Check if there are any .head() calls or sampling
        print("   Checking for common data limiting patterns...")
        
        # Test if clean_uploaded_dataframe has any limits
        from services.analytics_service import AnalyticsService
        import inspect
        
        # Get the source code of clean_uploaded_dataframe
        source = inspect.getsource(AnalyticsService.clean_uploaded_dataframe)
        
        if '.head(' in source:
            print("    FOUND .head() call in clean_uploaded_dataframe!")
        if '.sample(' in source:
            print("    FOUND .sample() call in clean_uploaded_dataframe!")
        if 'nrows' in source:
            print("    FOUND nrows parameter in clean_uploaded_dataframe!")
        if '150' in source:
            print("    FOUND hardcoded 150 in clean_uploaded_dataframe!")
            
        print("    Source code check complete")
        
    except Exception as e:
        print(f" Error checking source code: {e}")
    print()
    
    # Step 8: Final diagnosis
    print(" FINAL DIAGNOSIS")
    print("=" * 60)
    print("Key findings:")
    print("1. If you see ' FOUND 150 ROW LIMIT' above, that's the exact location")
    print("2. Most likely locations:")
    print("   - map_and_clean() function")
    print("   - clean_uploaded_dataframe() method")
    print("   - get_unique_patterns_analysis() method")
    print("3. The issue is in data processing, not display")


if __name__ == "__main__":
    test_unique_patterns_specific()
