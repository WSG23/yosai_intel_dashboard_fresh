"""Manual script to exercise selected API endpoints"""

import json
import os

import requests

# Test endpoints
API_PORT = os.getenv("API_PORT", "5001")
base_url = f"http://localhost:{API_PORT}"


def test_upload():
    """Test upload endpoint"""
    print("Testing upload endpoint...")
    # Create test data
    test_csv = "device_name,timestamp,bytes_sent\nrouter1,2024-01-01,1000\nswitch1,2024-01-01,2000"
    import base64

    contents = f"data:text/csv;base64,{base64.b64encode(test_csv.encode()).decode()}"

    response = requests.post(
        f"{base_url}/v1/upload",
        json={"contents": [contents], "filenames": ["test.csv"]},
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


if __name__ == "__main__":
    test_upload()
