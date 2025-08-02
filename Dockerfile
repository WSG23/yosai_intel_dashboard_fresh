FROM python:3.11-slim AS builder
WORKDIR /app

# Install dependencies
COPY requirements.txt requirements.lock ./
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.lock

# Copy source and setup scripts
COPY yosai_intel_dashboard/ ./yosai_intel_dashboard/
COPY scripts/ ./scripts/
COPY alembic.ini ./

# Create legacy symlinks
RUN python scripts/create_symlinks.py

# Final runtime image
FROM python:3.11-slim
WORKDIR /app
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH=/app:/app/yosai_intel_dashboard/src

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app /app

CMD ["python", "-m", "yosai_intel_dashboard.src.services.main"]

