"""Manual script to verify API endpoints are reachable"""

import json

import requests


def test_endpoints():
    base_url = "http://localhost:5000"

    endpoints = [
        "/api/health",
        "/api/v1/analytics/health",
        "/api/v1/analytics/patterns",
        "/api/v1/analytics/sources",
        "/api/v1/graphs/chart/patterns",
    ]

    print("Testing API endpoints...")

    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"{status} {endpoint} - Status: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"❌ {endpoint} - Connection failed (Flask not running?)")
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")


if __name__ == "__main__":
    test_endpoints()
