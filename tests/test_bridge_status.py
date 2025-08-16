import os
import importlib
from fastapi import FastAPI

os.environ["YOSAI_REALAPI_SPEC"] = "fastapi:FastAPI"
import mvp_api_bridge


def test_try_mount_real_api_updates_status():
    importlib.reload(mvp_api_bridge)
    app = FastAPI()
    mvp_api_bridge.try_mount_real_api(app)
    assert mvp_api_bridge._status["spec"] == "fastapi:FastAPI"
    assert mvp_api_bridge._status["mounted"] is True
    assert mvp_api_bridge._status["error"] is None
