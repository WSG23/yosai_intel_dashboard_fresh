import asyncio
import json
import os
import ssl
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

from shared.httpx import BreakerClient

CERT_DIR = Path(__file__).resolve().parents[2] / "deploy" / "k8s" / "certs"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b"{\"ok\": true}")


@pytest.fixture
def tls_server():
    server = HTTPServer(("127.0.0.1", 0), Handler)
    ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ctx.load_cert_chain(
        certfile=str(CERT_DIR / "gateway.crt"),
        keyfile=str(CERT_DIR / "gateway.key"),
    )
    ctx.load_verify_locations(cafile=str(CERT_DIR / "ca.crt"))
    ctx.verify_mode = ssl.CERT_REQUIRED
    server.socket = ctx.wrap_socket(server.socket, server_side=True)
    port = server.socket.getsockname()[1]
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        yield f"https://127.0.0.1:{port}"
    finally:
        server.shutdown()
        thread.join()


@pytest.mark.asyncio
async def test_tls_connection_validates_certificate(tls_server):
    os.environ["TLS_CERT_FILE"] = str(CERT_DIR / "httpx.crt")
    os.environ["TLS_KEY_FILE"] = str(CERT_DIR / "httpx.key")
    os.environ["TLS_CA_FILE"] = str(CERT_DIR / "ca.crt")
    client = BreakerClient()
    resp = await client.request("GET", tls_server)
    assert resp.json() == {"ok": True}
    await client.aclose()


@pytest.mark.asyncio
async def test_tls_connection_fails_without_client_cert(tls_server):
    os.environ.pop("TLS_CERT_FILE", None)
    os.environ.pop("TLS_KEY_FILE", None)
    os.environ["TLS_CA_FILE"] = str(CERT_DIR / "ca.crt")
    client = BreakerClient()
    with pytest.raises(Exception):
        await client.request("GET", tls_server)
    await client.aclose()
