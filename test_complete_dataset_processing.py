#!/usr/bin/env python3
"""
Test script to verify complete dataset processing works correctly
Run this after applying fixes to confirm 2000+ rows are processed
"""

import pandas as pd
import logging
import tempfile
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project path
sys.path.append(str(Path(__file__).parent))


def create_large_test_dataset(rows: int = 2500) -> pd.DataFrame:
    """Create a test dataset larger than typical batch limits"""
    
    logger.info(f"🏗️  Creating test dataset with {rows:,} rows")
    
    data = []
    base_date = datetime(2024, 1, 1)
    
    for i in range(rows):
        data.append({
            'row_id': i + 1,
            'person_id': f'USER_{(i % 150) + 1:03d}',  # 150 unique users
            'door_id': f'DOOR_{(i % 25) + 1:02d}',      # 25 unique doors
            'badge_id': f'BADGE_{(i % 200) + 1:04d}',   # 200 unique badges
            'access_result': random.choice(['Granted', 'Granted', 'Granted', 'Denied']),  # 75% granted
            'timestamp': (base_date + timedelta(minutes=i)).isoformat(),
            'door_held_time': round(random.uniform(0.5, 10.0), 2),
            'entry_without_badge': random.choice([True, False, False, False]),  # 25% no badge
            'device_status': random.choice(['normal', 'normal', 'normal', 'error']),  # 25% error
            'location': random.choice(['Building A', 'Building B', 'Building C']),
            'department': random.choice(['Engineering', 'Sales', 'HR', 'Marketing', 'Operations'])
        })
    
    df = pd.DataFrame(data)
    logger.info(f"✅ Dataset created: {len(df):,} rows × {len(df.columns)} columns")
    
    # Verify dataset properties
    assert len(df) == rows, f"Expected {rows} rows, got {len(df)}"
    assert df['person_id'].nunique() <= 150, "Too many unique users"
    assert df['door_id'].nunique() <= 25, "Too many unique doors"
    
    return df


def test_csv_processing_pipeline(df: pd.DataFrame) -> dict:
    """Test the complete CSV processing pipeline"""
    
    logger.info("🧪 TESTING CSV PROCESSING PIPELINE")
    
    results = {
        'input_rows': len(df),
        'steps_completed': [],
        'errors': [],
        'final_row_count': 0
    }
    
    # Create temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        csv_path = f.name
        df.to_csv(csv_path, index=False)
    
    try:
        # Step 1: Test file reading
        logger.info("Step 1: Testing raw CSV reading...")
        try:
            df_raw = pd.read_csv(csv_path)
            step1_rows = len(df_raw)
            results['steps_completed'].append(f"Step 1 - Raw read: {step1_rows:,} rows")
            logger.info(f"✅ Step 1: Read {step1_rows:,} rows")
            
            if step1_rows != results['input_rows']:
                results['errors'].append(f"Step 1: Row count mismatch - expected {results['input_rows']}, got {step1_rows}")
                
        except Exception as e:
            results['errors'].append(f"Step 1 failed: {e}")
            logger.error(f"❌ Step 1 failed: {e}")
            return results
        
        # Step 2: Test FileProcessor (if available)
        logger.info("Step 2: Testing FileProcessor...")
        try:
            from services.file_processor import FileProcessor
            
            processor = FileProcessor(upload_folder="temp", allowed_extensions={"csv"})
            processor_result = processor.process_file(
                open(csv_path, 'rb').read(), 
                os.path.basename(csv_path)
            )
            
            if processor_result.get('success'):
                step2_rows = processor_result.get('rows', 0)
                results['steps_completed'].append(f"Step 2 - FileProcessor: {step2_rows:,} rows")
                logger.info(f"✅ Step 2: FileProcessor processed {step2_rows:,} rows")
                
                if step2_rows != step1_rows:
                    results['errors'].append(f"Step 2: Row count changed - was {step1_rows}, now {step2_rows}")
            else:
                results['errors'].append(f"Step 2: FileProcessor failed - {processor_result.get('error')}")
                
        except ImportError:
            results['steps_completed'].append("Step 2 - FileProcessor: SKIPPED (not available)")
            logger.info("⏭️  Step 2: FileProcessor not available, skipping")
        except Exception as e:
            results['errors'].append(f"Step 2 failed: {e}")
            logger.error(f"❌ Step 2 failed: {e}")
        
        # Step 3: Test DataFrameValidator
        logger.info("Step 3: Testing DataFrameValidator...")
        try:
            from security.dataframe_validator import DataFrameSecurityValidator
            
            validator = DataFrameSecurityValidator()
            validated_df, needs_chunking = validator.validate_for_analysis(df_raw.copy())
            step3_rows = len(validated_df)
            
            results['steps_completed'].append(f"Step 3 - Validator: {step3_rows:,} rows (chunking: {needs_chunking})")
            logger.info(f"✅ Step 3: Validator processed {step3_rows:,} rows, chunking: {needs_chunking}")
            
            if step3_rows < step1_rows * 0.95:  # More than 5% data loss
                results['errors'].append(f"Step 3: Significant data loss - {step1_rows - step3_rows} rows removed")
                
        except ImportError:
            results['steps_completed'].append("Step 3 - Validator: SKIPPED (not available)")
            logger.info("⏭️  Step 3: DataFrameValidator not available, skipping")
        except Exception as e:
            results['errors'].append(f"Step 3 failed: {e}")
            logger.error(f"❌ Step 3 failed: {e}")
        
        # Step 4: Test AnalyticsService (if available)
        logger.info("Step 4: Testing AnalyticsService...")
        try:
            from services.analytics_service import AnalyticsService
            
            analytics = AnalyticsService()
            
            # Test with validated DataFrame if available, otherwise use raw
            test_df = validated_df if 'validated_df' in locals() else df_raw
            
            result = analytics.analyze_with_chunking(test_df.copy(), ["basic"])
            step4_rows = result.get("processing_summary", {}).get("rows_processed", "UNKNOWN")
            
            results['steps_completed'].append(f"Step 4 - Analytics: {step4_rows} rows processed")
            logger.info(f"✅ Step 4: Analytics processed {step4_rows} rows")
            
            results['final_row_count'] = step4_rows if isinstance(step4_rows, int) else len(test_df)
            
        except ImportError:
            results['steps_completed'].append("Step 4 - Analytics: SKIPPED (not available)")
            logger.info("⏭️  Step 4: AnalyticsService not available, skipping")
        except Exception as e:
            results['errors'].append(f"Step 4 failed: {e}")
            logger.error(f"❌ Step 4 failed: {e}")
    
    finally:
        # Clean up temporary file
        try:
            os.unlink(csv_path)
        except:
            pass
    
    return results


def verify_configuration():
    """Verify that configuration supports large dataset processing"""
    
    logger.info("⚙️  VERIFYING CONFIGURATION")
    
    try:
        from config.dynamic_config import dynamic_config
        
        config_issues = []
        
        # Check analytics configuration
        if hasattr(dynamic_config, 'analytics'):
            analytics = dynamic_config.analytics
            
            if hasattr(analytics, 'force_full_dataset_analysis'):
                if not analytics.force_full_dataset_analysis:
                    config_issues.append("analytics.force_full_dataset_analysis is False")
            else:
                config_issues.append("analytics.force_full_dataset_analysis not set")
            
            if hasattr(analytics, 'max_records_per_query'):
                if analytics.max_records_per_query < 100000:
                    config_issues.append(f"analytics.max_records_per_query too low: {analytics.max_records_per_query}")
            
            if hasattr(analytics, 'batch_size'):
                if analytics.batch_size < 1000:
                    config_issues.append(f"analytics.batch_size too low: {analytics.batch_size}")
        else:
            config_issues.append("analytics configuration missing")
        
        # Check security configuration
        if hasattr(dynamic_config, 'security'):
            security = dynamic_config.security
            
            if hasattr(security, 'max_upload_mb'):
                if security.max_upload_mb < 50:
                    config_issues.append(f"security.max_upload_mb too low: {security.max_upload_mb}")
        
        if config_issues:
            logger.warning("⚠️  Configuration issues found:")
            for issue in config_issues:
                logger.warning(f"    • {issue}")
        else:
            logger.info("✅ Configuration looks good for large dataset processing")
            
        return len(config_issues) == 0
        
    except ImportError:
        logger.warning("⚠️  Could not import dynamic_config for verification")
        return False


def main():
    """Run complete test suite"""
    
    logger.info("🚀 COMPLETE DATASET PROCESSING TEST")
    logger.info("=" * 70)
    
    # Step 1: Verify configuration
    config_ok = verify_configuration()
    
    logger.info("\n" + "=" * 70)
    
    # Step 2: Create test dataset
    test_df = create_large_test_dataset(rows=2500)
    
    logger.info("\n" + "=" * 70)
    
    # Step 3: Test processing pipeline
    results = test_csv_processing_pipeline(test_df)
    
    logger.info("\n" + "=" * 70)
    logger.info("📊 TEST RESULTS SUMMARY")
    logger.info("=" * 70)
    
    logger.info(f"Input rows: {results['input_rows']:,}")
    logger.info(f"Final processed rows: {results['final_row_count']:,}")
    
    logger.info("\nSteps completed:")
    for step in results['steps_completed']:
        logger.info(f"  ✅ {step}")
    
    if results['errors']:
        logger.warning(f"\n❌ {len(results['errors'])} errors found:")
        for error in results['errors']:
            logger.warning(f"  • {error}")
    else:
        logger.info("\n🎉 No errors found!")
    
    # Final assessment
    success_rate = results['final_row_count'] / results['input_rows'] if results['final_row_count'] else 0
    
    if success_rate >= 0.99:  # 99% or more rows processed
        logger.info(f"🎯 SUCCESS! {success_rate:.1%} of data processed correctly")
    elif success_rate >= 0.90:
        logger.warning(f"⚠️  PARTIAL SUCCESS: {success_rate:.1%} of data processed (some data loss)")
    else:
        logger.error(f"❌ FAILURE: Only {success_rate:.1%} of data processed")
    
    return success_rate >= 0.99


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)