from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="MVP API")

@app.get("/healthz")
def healthz():
    return {"ok": True}

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/api/login")
def login(body: LoginRequest):
    return {"token": "dev-token", "user": {"name": body.username}}

@app.get("/api/analytics/summary")
def analytics_summary():
    return {"total": 42, "trend": [1, 2, 3, 4]}
