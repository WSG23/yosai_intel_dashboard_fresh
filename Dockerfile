# syntax=docker/dockerfile:1

ARG PYTHON_IMAGE="python:3.11-slim@sha256:0ce77749ac83174a31d5e107ce0cfa6b28a2fd6b0615e029d9d84b39c48976ee"
# hadolint ignore=DL3006
FROM ${PYTHON_IMAGE} AS builder
WORKDIR /app

# Install system packages
# hadolint ignore=DL3008
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN python -m venv /opt/venv \
    && grep -v '^apache-flink' requirements.txt > requirements.filtered \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.filtered

# hadolint ignore=DL3006
FROM ${PYTHON_IMAGE}

# Install runtime packages
# hadolint ignore=DL3008
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH=/app:/app/src:/app/yosai_intel_dashboard/src

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
COPY --chown=appuser:appuser . /app
RUN chmod 0755 docker-entrypoint.sh \
    && find /app -type f -name '*.sh' -exec chmod 0755 {} \; \
    && find /app -type f \( -name '*.yaml' -o -name '*.yml' -o -name '*.conf' \) -exec chmod 0644 {} \; \
    && rm -rf /app/yosai_intel_dashboard/tests
USER appuser

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["src/start_api.py"]
HEALTHCHECK --interval=30s --timeout=10s CMD curl --fail http://localhost:8000/health || exit 1
