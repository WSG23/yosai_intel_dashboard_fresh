from fastapi import FastAPI
from pydantic import BaseModel

from services.analytics_service import create_analytics_service

app = FastAPI(title="Analytics Microservice")
service = create_analytics_service()

class PatternsRequest(BaseModel):
    days: int = 7

@app.post("/api/v1/analytics/get_dashboard_summary")
async def dashboard_summary():
    return service.get_dashboard_summary()

@app.post("/api/v1/analytics/get_access_patterns_analysis")
async def access_patterns(req: PatternsRequest):
    return service.get_access_patterns_analysis(days=req.days)
