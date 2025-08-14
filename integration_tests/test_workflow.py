import base64
import time
import requests


def wait_for_service(url: str, timeout: int = 60) -> None:
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code < 500:
                return
        except Exception:
            pass
        time.sleep(1)
    raise RuntimeError(f"service {url} not ready")


def test_upload_and_analytics():
    gateway_url = "http://localhost:8081"
    wait_for_service(f"{gateway_url}/metrics")

    content = b"a,b\n1,2\n"
    b64 = base64.b64encode(content).decode()
    data_url = f"data:text/csv;base64,{b64}"

    resp = requests.post(
        f"{gateway_url}/v1/upload",
        json={"contents": [data_url], "filenames": ["test.csv"]},
        timeout=30,
    )
    assert resp.status_code == 200

    resp = requests.get(
        f"{gateway_url}/v1/analytics/dashboard-summary", timeout=30
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "success"
