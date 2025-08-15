import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from yosai_intel_dashboard.src.adapters.api.adapter import create_api_app

app = create_api_app()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/docs")

def custom_openapi():
    if getattr(app, "openapi_schema", None):
        return app.openapi_schema
    schema = get_openapi(title=getattr(app, "title", "Dashboard"), version=getattr(app, "version", "0.1.0"), routes=app.routes)
    schema["servers"] = [{"url": "http://localhost:8050"}]
    app.openapi_schema = schema
    return app.openapi_schema

app.openapi = custom_openapi
