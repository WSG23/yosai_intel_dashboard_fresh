# syntax=docker/dockerfile:1

FROM python:3.11-slim AS builder
RUN mkdir /wheels \
    && pip wheel --wheel-dir=/wheels requests

FROM python:3.11-slim
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels
