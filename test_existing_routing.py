from core.app_factory import create_app

# Use your existing app factory
app = create_app()

# Create a simple upload page that works with existing routing
import pages.file_upload_simple_backup as simple_upload

# Temporarily replace the upload page with the simple working one
import pages.file_upload as current_upload
import sys

# Backup current module
sys.modules['pages.file_upload_original'] = current_upload

# Replace with simple version  
sys.modules['pages.file_upload'] = simple_upload

if __name__ == "__main__":
    app.run_server(debug=True, port=8053)
