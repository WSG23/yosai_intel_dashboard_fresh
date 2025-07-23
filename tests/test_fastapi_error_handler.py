from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse
from yosai_framework.errors import ServiceError, error_response
from shared.errors.types import ErrorCode

app = FastAPI()


@app.get("/fail")
async def fail():
    body, status = error_response(ServiceError(ErrorCode.INVALID_INPUT, "bad"))
    return JSONResponse(content=body, status_code=status)


client = TestClient(app)


def test_fastapi_error_format():
    resp = client.get("/fail")
    assert resp.status_code == 400
    assert resp.json() == {"code": "invalid_input", "message": "bad"}
