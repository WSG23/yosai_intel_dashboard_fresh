FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn kafka-python prometheus-fastapi-instrumentator opentelemetry-instrumentation-fastapi

COPY . .
RUN python scripts/create_symlinks.py

ENV PYTHONPATH=/app:/app/yosai_intel_dashboard/src

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
