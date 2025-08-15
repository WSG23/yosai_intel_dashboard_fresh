# syntax=docker/dockerfile:1

ARG BASE_IMAGE="yosai-base"
FROM ${BASE_IMAGE}

ENV PYTHONPATH=/app:/app/src:/app/yosai_intel_dashboard/src
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
