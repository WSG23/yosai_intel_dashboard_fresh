from __future__ import annotations

import pathlib
import shutil
import subprocess
import time

import pytest
import requests

MANIFEST_DIR = pathlib.Path("k8s/services")
if not MANIFEST_DIR.exists():
    MANIFEST_DIR = pathlib.Path("k8s/microservices")


class K8sResolver:
    """Simple resolver using kubectl"""

    def resolve(self, name: str, namespace: str = "default") -> str:
        out = subprocess.check_output(
            [
                "kubectl",
                "get",
                "svc",
                name,
                "-n",
                namespace,
                "-o",
                "jsonpath={.spec.clusterIP}:{.spec.ports[0].port}",
            ]
        )
        return out.decode().strip()


def _wait_ready(label: str, timeout: int = 120) -> None:
    end = time.time() + timeout
    while time.time() < end:
        res = subprocess.run(
            [
                "kubectl",
                "get",
                "pods",
                "-l",
                f"app={label}",
                "-o",
                "jsonpath={.items[0].status.containerStatuses[0].ready}",
            ],
            capture_output=True,
            text=True,
        )
        if res.stdout.strip() == "true":
            return
        time.sleep(3)
    raise RuntimeError(f"{label} not ready")


@pytest.fixture(scope="session")
def kind_cluster(request):
    if not shutil.which("kind") or not shutil.which("kubectl"):
        pytest.skip("kind or kubectl not available")

    cluster_name = "yd-test"
    subprocess.run(["kind", "create", "cluster", "--name", cluster_name], check=True)

    def fin():
        subprocess.run(
            ["kind", "delete", "cluster", "--name", cluster_name], check=True
        )

    request.addfinalizer(fin)
    return cluster_name


@pytest.fixture(scope="session")
def deploy_manifests(kind_cluster, request):
    subprocess.run(["kubectl", "apply", "-f", str(MANIFEST_DIR)], check=True)

    def fin():
        subprocess.run(["kubectl", "delete", "-f", str(MANIFEST_DIR)], check=True)

    request.addfinalizer(fin)


@pytest.mark.integration
def test_k8s_resolver_and_health(kind_cluster, deploy_manifests):
    _wait_ready("api-gateway")

    resolver = K8sResolver()
    addr = resolver.resolve("api-gateway")
    assert addr

    proc = subprocess.Popen(
        ["kubectl", "port-forward", "service/api-gateway", "8080:80"]
    )
    try:
        for _ in range(20):
            try:
                r = requests.get("http://localhost:8080/health", timeout=3)
                if r.status_code == 200:
                    break
            except requests.RequestException:
                time.sleep(1)
        else:
            pytest.fail("Health endpoint did not respond")
        assert r.json().get("status") == "ok"
    finally:
        proc.terminate()
        proc.wait()
