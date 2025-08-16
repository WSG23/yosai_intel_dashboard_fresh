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
