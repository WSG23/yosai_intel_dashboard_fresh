from __future__ import annotations
import asyncio, json, os
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Depends, UploadFile, File, Response, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from services.enrich_service import enrich_csv_content
from services.stream_service import event_stream

load_dotenv()
app = FastAPI()

@app.get("/healthz")
def healthz():
    return {"ok": True}

def _auth_header(authorization: str = Header(default="")) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.split(" ", 1)[1].strip()
    if token != "dev-token":
        raise HTTPException(status_code=401, detail="Invalid token")
    return token

def _auth_header_or_query(
    authorization: str = Header(default=""),
    token: str | None = Query(default=None),
) -> str:
    if token:
        if token != "dev-token":
            raise HTTPException(status_code=401, detail="Invalid token")
        return token
    return _auth_header(authorization)

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/api/login")
def login(body: LoginRequest):
    return {"token": "dev-token", "user": {"name": body.username}}

@app.get("/api/analytics/summary")
def analytics_summary(_: str = Depends(_auth_header)):
    return {"total": 42, "trend": [1,2,3,4,5,4,6]}

@app.api_route("/api/export", methods=["GET","HEAD"])
def export_csv(_: str = Depends(_auth_header)):
    csv = "id,name,value\n1,Alice,10\n2,Bob,20\n3,Carol,30\n"
    return Response(
        content=csv,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=export.csv"}
    )

@app.post("/api/upload")
async def upload_csv(file: UploadFile = File(...), _: str = Depends(_auth_header)):
    text = (await file.read()).decode("utf-8", errors="ignore")
    out = enrich_csv_content(text)
    return {"filename": file.filename, **out}

@app.get("/api/events")
async def events(_: str = Depends(_auth_header_or_query)):
    async def gen():
        async for item in event_stream("dev-token"):
            yield f"data: {json.dumps(item)}\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream")

from mvp_api_bridge import try_mount_real_api
_mounted = try_mount_real_api(app)

from mvp_api_bridge import mount_real
try:
    _spec=open("mvp_api_bridge_spec.txt").read().strip()
except Exception:
    _spec=""
mounted = mount_real(app, _spec)


# BEGIN REALAPI MOUNT
import importlib
def _load_realapi(spec: str):
    mod, _, attr = spec.partition(":")
    m = importlib.import_module(mod)
    obj = getattr(m, attr) if attr else getattr(m, "app", None)
    return obj() if callable(obj) else obj
try:
    _SPEC = 'venv.lib.python3.11.site-packages.prefect.server.api.server:create_api_app'
    if _SPEC:
        _real = _load_realapi(_SPEC)
        if _real:
            app.mount("/realapi", _real)
except Exception as _e:
    pass
# END REALAPI MOUNT

