# syntax=docker/dockerfile:1

FROM python:3.11-slim@sha256:0ce77749ac83174a31d5e107ce0cfa6b28a2fd6b0615e029d9d84b39c48976ee AS builder
WORKDIR /app

# Install system packages
RUN apt-get update \ 
    && apt-get install -y --no-install-recommends build-essential curl \ 
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY ../requirements.txt ./
RUN python -m venv /opt/venv \
    && . /opt/venv/bin/activate \
    && grep -v '^apache-flink' requirements.txt > requirements.filtered \
    && pip install --no-cache-dir -r requirements.filtered

FROM python:3.11-slim@sha256:0ce77749ac83174a31d5e107ce0cfa6b28a2fd6b0615e029d9d84b39c48976ee
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH=/app:/app/yosai_intel_dashboard/src

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

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
COPY ../docker-entrypoint.sh ./docker-entrypoint.sh
COPY ../start_api.py ./start_api.py
RUN chmod +x docker-entrypoint.sh \
    && rm -rf /app/yosai_intel_dashboard/tests \
    && chown -R appuser:appuser /app
USER appuser

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["start_api.py"]
