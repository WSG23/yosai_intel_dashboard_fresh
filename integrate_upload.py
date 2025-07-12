#!/usr/bin/env python3
"""
Integration script - adds file upload to your main app
"""

# Add this to your pages/file_upload.py or wherever you need uploaded files
def get_uploaded_files_from_flask():
    """Get files uploaded via Flask endpoint"""
    try:
        import requests
        response = requests.get('http://localhost:5001/files')
        if response.status_code == 200:
            return response.json()['files']
    except:
        pass
    return []

# Add this to your analytics page to get uploaded data
def get_uploaded_dataframes():
    """Get actual dataframes from uploaded files"""
    from upload_handler import get_uploaded_files_simple
    return get_uploaded_files_simple()

print("✅ Integration functions ready")
print("Usage in your Dash app:")
print("  files = get_uploaded_files_from_flask()")
print("  dataframes = get_uploaded_dataframes()")
