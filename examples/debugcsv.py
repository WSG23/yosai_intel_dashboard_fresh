#!/usr/bin/env python3
"""
Debug script to identify exactly where your CSV is being truncated
Run this to find the source of the 5-row limitation
"""

import sys
import pandas as pd
import base64
import io
import logging
from pathlib import Path

# Add your project to path
sys.path.append('.')

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_csv_file_directly(csv_path: str):
    """Test reading your actual CSV file directly"""
    logger.info(f" Testing direct CSV read: {csv_path}")
    
    try:
        # Test 1: Direct pandas read
        df_direct = pd.read_csv(csv_path)
        logger.info(f" Direct pd.read_csv(): {len(df_direct)} rows × {len(df_direct.columns)} columns")
        
        # Test 2: Read raw file content
        with open(csv_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        logger.info(f" Raw file read: {len(lines)} lines total")
        
        # Test 3: Check first few lines
        logger.info(f" First 3 lines of CSV:")
        for i, line in enumerate(lines[:3]):
            logger.info(f"   Line {i+1}: {line.strip()}")
        
        return len(df_direct), len(lines)
        
    except Exception as e:
        logger.error(f" Error reading CSV directly: {e}")
        return 0, 0

def test_base64_encoding(csv_path: str):
    """Test base64 encoding process (simulating file upload)"""
    logger.info(f" Testing base64 encoding process...")
    
    try:
        # Step 1: Read file as bytes (simulating upload)
        with open(csv_path, 'rb') as f:
            file_bytes = f.read()
        
        logger.info(f" File size: {len(file_bytes)} bytes")
        
        # Step 2: Base64 encode (simulating browser upload)
        encoded = base64.b64encode(file_bytes).decode('utf-8')
        contents = f"data:text/csv;base64,{encoded}"
        
        logger.info(f" Base64 encoded length: {len(encoded)} characters")
        
        # Step 3: Decode back (simulating server processing)
        content_type, content_string = contents.split(',', 1)
        decoded = base64.b64decode(content_string)
        
        logger.info(f" Decoded back to: {len(decoded)} bytes")
        
        # Step 4: Parse as CSV
        text = decoded.decode('utf-8')
        lines = text.split('\n')
        logger.info(f" Decoded text has: {len(lines)} lines")
        
        # Step 5: Parse with pandas
        df = pd.read_csv(io.StringIO(text))
        logger.info(f" Pandas read from StringIO: {len(df)} rows × {len(df.columns)} columns")
        
        return len(df)
        
    except Exception as e:
        logger.error(f" Error in base64 encoding test: {e}")
        return 0

def test_file_validator():
    """Test the file validator that might be truncating your CSV"""
    logger.info(f" Testing file validator...")
    
    try:
        from utils.file_validator import process_dataframe
        
        # Create test CSV data
        test_data = []
        for i in range(100):  # Create 100 rows
            test_data.append(f"row_{i},value_{i},data_{i}\n")
        
        test_csv = "id,name,value\n" + "".join(test_data)
        test_bytes = test_csv.encode('utf-8')
        
        logger.info(f" Created test CSV: {len(test_csv.split(chr(10)))} lines")
        
        # Test the validator
        df, error = process_dataframe(test_bytes, "test.csv")
        
        if df is not None:
            logger.info(f" File validator result: {len(df)} rows × {len(df.columns)} columns")
            if len(df) < 90:  # Should have ~100 rows
                logger.warning(f" FILE VALIDATOR IS TRUNCATING DATA!")
                logger.warning(f"   Expected ~100 rows, got {len(df)}")
        else:
            logger.error(f" File validator failed: {error}")
        
        return len(df) if df is not None else 0
        
    except ImportError:
        logger.warning(" Could not import file validator for testing")
        return 0
    except Exception as e:
        logger.error(f" Error testing file validator: {e}")
        return 0

def test_upload_service(csv_path: str):
    """Test the complete upload service pipeline"""
    logger.info(f" Testing upload service pipeline...")
    
    try:
        from services.upload_service import process_uploaded_file
        
        # Step 1: Prepare file as base64 (simulating upload)
        with open(csv_path, 'rb') as f:
            file_bytes = f.read()
        
        encoded = base64.b64encode(file_bytes).decode('utf-8')
        contents = f"data:text/csv;base64,{encoded}"
        filename = Path(csv_path).name
        
        logger.info(f" Prepared upload: {filename}, {len(file_bytes)} bytes")
        
        # Step 2: Process through upload service
        result = process_uploaded_file(contents, filename)
        
        if result.get('success'):
            rows = result.get('rows', 0)
            cols = len(result.get('columns', []))
            logger.info(f" Upload service result: {rows} rows × {cols} columns")
            
            if rows < 20:  # Your file should have 2000+ rows
                logger.warning(f" UPLOAD SERVICE IS TRUNCATING DATA!")
                logger.warning(f"   Expected 2000+ rows, got {rows}")
            else:
                logger.info(f" Upload service working correctly!")
        else:
            logger.error(f" Upload service failed: {result.get('error')}")
            return 0
        
        return result.get('rows', 0)
        
    except ImportError:
        logger.warning(" Could not import upload service for testing")
        return 0
    except Exception as e:
        logger.error(f" Error testing upload service: {e}")
        return 0

def main():
    """Run complete diagnostic"""
    logger.info(" CSV TRUNCATION DIAGNOSTIC")
    logger.info("=" * 60)
    
    # Get CSV file path from user
    csv_path = input("Enter path to your CSV file (or press Enter for demo): ").strip()
    
    if not csv_path:
        # Create a demo CSV
        demo_data = "Timestamp,Person ID,Token ID,Device name,Access result\n"
        for i in range(2000):
            demo_data += f"2024-01-01 10:{i%60:02d}:00,USER_{i%100:03d},TOKEN_{i%500:04d},DOOR_{i%10:02d},{'Granted' if i%4 != 0 else 'Denied'}\n"
        
        csv_path = "debug_demo.csv"
        with open(csv_path, 'w') as f:
            f.write(demo_data)
        logger.info(f" Created demo CSV: {csv_path} with 2000 rows")
    
    if not Path(csv_path).exists():
        logger.error(f" File not found: {csv_path}")
        return
    
    # Run diagnostic tests
    logger.info(f"\n{'='*60}")
    
    # Test 1: Direct file reading
    direct_rows, file_lines = test_csv_file_directly(csv_path)
    
    logger.info(f"\n{'='*60}")
    
    # Test 2: Base64 encoding/decoding
    base64_rows = test_base64_encoding(csv_path)
    
    logger.info(f"\n{'='*60}")
    
    # Test 3: File validator
    validator_rows = test_file_validator()
    
    logger.info(f"\n{'='*60}")
    
    # Test 4: Upload service
    upload_rows = test_upload_service(csv_path)
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info(" DIAGNOSTIC SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"1. Direct file read:     {direct_rows:,} rows ({file_lines:,} lines)")
    logger.info(f"2. Base64 process:       {base64_rows:,} rows")
    logger.info(f"3. File validator:       {validator_rows:,} rows")
    logger.info(f"4. Upload service:       {upload_rows:,} rows")
    
    # Analysis
    if direct_rows > 100 and upload_rows < 20:
        logger.error("\n ISSUE IDENTIFIED:")
        logger.error("   Your CSV file is being truncated during upload processing!")
        logger.error("   The file has 2000+ rows but only 5 reach the final stage.")
        
        if validator_rows < direct_rows:
            logger.error("   → Problem is in the FILE VALIDATOR")
        elif upload_rows < base64_rows:
            logger.error("   → Problem is in the UPLOAD SERVICE")
        else:
            logger.error("   → Problem is somewhere else in the pipeline")
            
    elif upload_rows > 100:
        logger.info("\n UPLOAD PIPELINE IS WORKING CORRECTLY!")
        logger.info("   The issue might be in your UI display or a cached result.")
        
    else:
        logger.warning("\n INCONCLUSIVE RESULTS")
        logger.warning("   Please check the individual test results above.")

if __name__ == "__main__":
    main()
