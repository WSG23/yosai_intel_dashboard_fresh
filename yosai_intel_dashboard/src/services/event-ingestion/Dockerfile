FROM python:3.11-slim

RUN pip install --no-cache-dir fastapi uvicorn kafka-python prometheus-fastapi-instrumentator opentelemetry-instrumentation-fastapi

ARG UID=1000
ARG GID=1000
RUN set -eux; \
    if command -v addgroup >/dev/null 2>&1; then \
      addgroup -g "${GID}" appuser || true; \
      adduser -D -u "${UID}" -G appuser appuser 2>/dev/null || adduser --uid "${UID}" --gid "${GID}" --disabled-password --gecos "" appuser; \
    else \
      groupadd -g "${GID}" appuser || true; \
      useradd -m -u "${UID}" -g "${GID}" appuser || true; \
    fi
WORKDIR /app
COPY . /app
RUN python scripts/create_symlinks.py && chown -R appuser:appuser /app
ENV PYTHONPATH=/app:/app/yosai_intel_dashboard/src
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD curl -f http://localhost:8000/health || exit 1
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
