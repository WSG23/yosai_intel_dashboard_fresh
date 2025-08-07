# syntax=docker/dockerfile:1

FROM python:3.11-slim AS builder
WORKDIR /app

# Install system packages
RUN apt-get update \ 
    && apt-get install -y --no-install-recommends build-essential curl \ 
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN python -m venv /opt/venv \
    && . /opt/venv/bin/activate \
    && grep -v '^apache-flink' requirements.txt > requirements.filtered \
    && pip install --no-cache-dir -r requirements.filtered

FROM python:3.11-slim
WORKDIR /app
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH=/app:/app/yosai_intel_dashboard/src

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app/yosai_intel_dashboard /app/yosai_intel_dashboard
COPY docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh \
    && rm -rf /app/yosai_intel_dashboard/tests

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["start_api.py"]
