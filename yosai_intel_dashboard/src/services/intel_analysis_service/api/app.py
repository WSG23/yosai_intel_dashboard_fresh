"""FastAPI application for the intel analysis service UI gateway."""

from fastapi import FastAPI

from .ui import router as ui_router

app = FastAPI(title="Intel Analysis Service")
app.include_router(ui_router, prefix="/ui")
