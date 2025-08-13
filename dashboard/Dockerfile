# syntax=docker/dockerfile:1

FROM python:3.11-slim@sha256:0ce77749ac83174a31d5e107ce0cfa6b28a2fd6b0615e029d9d84b39c48976ee AS builder

WORKDIR /app

# Install system packages
# hadolint ignore=DL3008
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY ../requirements.txt ./
# hadolint ignore=SC1091
RUN python -m venv /opt/venv \
    && grep -v '^apache-flink' requirements.txt > requirements.filtered \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.filtered

FROM python:3.11-slim@sha256:0ce77749ac83174a31d5e107ce0cfa6b28a2fd6b0615e029d9d84b39c48976ee

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH=/app:/app/yosai_intel_dashboard/src

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

ARG UID=1000
ARG GID=1000
RUN set -eux; \
    if command -v addgroup >/dev/null 2>&1; then \
      addgroup -g "${GID}" appuser || true; \
      # hadolint ignore=DL3046
      adduser -D -u "${UID}" -G appuser appuser 2>/dev/null || adduser --uid "${UID}" --gid "${GID}" --disabled-password --gecos "" appuser; \
    else \
      groupadd -g "${GID}" appuser || true; \
      # hadolint ignore=DL3046
      useradd -l -m -u "${UID}" -g "${GID}" appuser || true; \
    fi
WORKDIR /app
COPY . /app
COPY ../core /app/core
COPY ../docker-entrypoint.sh ./docker-entrypoint.sh
RUN chmod 0755 docker-entrypoint.sh \
    && find /app -type f -name '*.sh' -exec chmod 0755 {} \; \
    && find /app -type f \( -name '*.yaml' -o -name '*.yml' -o -name '*.conf' \) -exec chmod 0644 {} \; \
    && rm -rf /app/yosai_intel_dashboard/tests \
    && chown -R appuser:appuser /app
USER appuser

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["python", "-m", "yosai_intel_dashboard.src.app"]
