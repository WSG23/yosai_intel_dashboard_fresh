import requests
import json

# Test endpoints
base_url = "http://localhost:5001"

def test_upload():
    """Test upload endpoint"""
    print("Testing upload endpoint...")
    # Create test data
    test_csv = "device_name,timestamp,bytes_sent\nrouter1,2024-01-01,1000\nswitch1,2024-01-01,2000"
    import base64
    contents = f"data:text/csv;base64,{base64.b64encode(test_csv.encode()).decode()}"
    
    response = requests.post(
        f"{base_url}/api/v1/upload",
        json={"contents": [contents], "filenames": ["test.csv"]}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

if __name__ == "__main__":
    test_upload()
