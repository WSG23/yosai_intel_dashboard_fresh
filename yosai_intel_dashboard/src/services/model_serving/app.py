"""FastAPI application exposing versioned model prediction endpoints.

The service uses :class:`ModelService` to manage registered models and provides
async `/predict` routes for inference.  Offloading inference to worker threads
allows the server to handle multiple requests concurrently and makes it possible
for the underlying models to utilise multiple CPU cores or GPU acceleration when
available.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI

from yosai_intel_dashboard.src.adapters.api.model_router import create_model_router
from yosai_intel_dashboard.src.services.model_service import ModelService


def create_app(registry_path: Optional[Path] = None) -> FastAPI:
    """Create the model serving :class:`FastAPI` application.

    Parameters
    ----------
    registry_path:
        Optional path to a model registry JSON file.  When not provided the
        default location within the container is used.
    """

    service = ModelService(registry_path=registry_path)
    app = FastAPI(title="Model Serving Service")
    app.include_router(create_model_router(service))
    return app


app = create_app()

__all__ = ["app", "create_app"]
