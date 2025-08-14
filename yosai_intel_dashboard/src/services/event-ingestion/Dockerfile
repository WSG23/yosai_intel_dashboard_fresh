FROM python:3.11-slim@sha256:0ce77749ac83174a31d5e107ce0cfa6b28a2fd6b0615e029d9d84b39c48976ee

# Install curl for health checks
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir fastapi uvicorn kafka-python prometheus-fastapi-instrumentator opentelemetry-instrumentation-fastapi

ARG UID=1000
ARG GID=1000
RUN set -eux; \
    if addgroup --help 2>&1 | grep -q BusyBox; then \
        addgroup -g "${GID}" appuser; \
        adduser -D -u "${UID}" -G appuser appuser; \
    else \
        groupadd --gid "${GID}" appuser; \
        useradd --no-create-home --uid "${UID}" --gid "${GID}" appuser; \
    fi
WORKDIR /app
COPY . /app
RUN python scripts/create_symlinks.py && chown -R appuser:appuser /app
ENV PYTHONPATH=/app:/app/yosai_intel_dashboard/src
USER appuser
EXPOSE 8000
# Use curl to verify the service is up
HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD curl --fail http://localhost:8000/health || exit 1
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
