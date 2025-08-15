import os
import sys
import traceback
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Ensure project root on path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

app = FastAPI(title="Dashboard Shim", version="0.1.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

BOOT_ERROR = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/docs")


@app.get("/_boot_error", include_in_schema=False)
def boot_error():
    if BOOT_ERROR:
        return JSONResponse(
            {"error": "import_failed", "detail": BOOT_ERROR}, status_code=500
        )
    return JSONResponse({"error": "none"}, status_code=404)


def _mount_full_app():
    global BOOT_ERROR
    try:
        from yosai_intel_dashboard.src.adapters.api.adapter import create_api_app

        full = create_api_app()
        app.mount("/app", full)
    except Exception:
        BOOT_ERROR = traceback.format_exc()


@app.on_event("startup")
async def startup():
    if os.getenv("DISABLE_FULL_APP", "0") != "1":
        _mount_full_app()
