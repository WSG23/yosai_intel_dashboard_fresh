import os
os.environ['DB_PASSWORD'] = 'dummy_for_testing'

from core.app_factory import create_app
import threading
import time
import requests

# Create app
print("Creating app...")
app = create_app(mode='full')
print("✅ App created")

# Check if nuclear fix messages appeared
print("\n🔍 Look for 'NUCLEAR FIX' messages above ☝️")

# Start server in thread
def run_server():
    app.run_server(debug=False, port=8052, use_reloader=False)

print("\nStarting server on port 8052...")
server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()
time.sleep(3)

# Test the endpoint
print("\n🧪 Testing /_dash-dependencies endpoint...")
try:
    response = requests.get('http://127.0.0.1:8052/_dash-dependencies')
    print(f"✅ Status Code: {response.status_code}")
    print(f"✅ Content-Type: {response.headers.get('Content-Type', 'NOT SET')}")
    
    # Check if response is empty array (nuclear fix working)
    if response.text.strip() == "[]":
        print("🎉 NUCLEAR FIX IS WORKING! Response is empty array: []")
    else:
        print(f"❌ NUCLEAR FIX NOT WORKING! Response has {len(response.text)} chars")
        print(f"First 200 chars: {response.text[:200]}...")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n✅ Test complete!")
