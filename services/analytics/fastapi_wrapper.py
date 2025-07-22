from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
from typing import Dict, Any

app = FastAPI(title="Analytics Service")

class AnalyticsRequest(BaseModel):
    query_type: str
    parameters: Dict[str, Any]

@app.post("/analyze")
async def analyze(request: AnalyticsRequest):
    from services.analytics_service import AnalyticsService
    service = AnalyticsService()
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(None, service.process_request, request.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
