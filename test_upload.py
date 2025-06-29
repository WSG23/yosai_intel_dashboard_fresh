#!/usr/bin/env python3
"""
Simple upload test - Creates a test CSV file to verify upload functionality
"""
import csv
import tempfile
import os
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

def create_test_csv():
    """Create a simple test CSV file for upload testing"""
    
    # Create test data
    test_data = [
        ['device_name', 'user_name', 'timestamp', 'access_type'],
        ['Door_A1', 'John_Smith', '2025-06-28 10:00:00', 'entry'],
        ['Door_B2', 'Jane_Doe', '2025-06-28 10:05:00', 'exit'],
        ['Door_C3', 'Bob_Wilson', '2025-06-28 10:10:00', 'entry'],
        ['Door_A1', 'Alice_Brown', '2025-06-28 10:15:00', 'exit'],
        ['Door_D4', 'Mike_Davis', '2025-06-28 10:20:00', 'entry'],
    ]
    
    # Create test file in current directory
    test_file = Path("test_upload_data.csv")
    
    with open(test_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(test_data)
    
    logger.info(f"✅ Created test file: {test_file.absolute()}")
    logger.info(f"📄 File contains {len(test_data)-1} data rows")
    logger.info("🔧 Use this file to test the upload functionality")
    logger.info("\n📋 Next steps:")
    logger.info("1. Start the app: python3 app.py")
    logger.info("2. Go to: http://127.0.0.1:8050/upload")
    logger.info("3. Upload the test_upload_data.csv file")
    logger.info("4. Check logs for upload processing messages")
    
    return test_file

if __name__ == "__main__":
    create_test_csv()