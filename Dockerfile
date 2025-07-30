FROM python:3.11-slim as builder
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies in a virtual environment
COPY requirements.txt .
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

FROM python:3.11-slim
WORKDIR /app
ENV PATH="/opt/venv/bin:$PATH"

# Copy virtual env and application from builder stage
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app /app

# Create non-root user
RUN groupadd --system app && useradd --system --gid app app
USER app

ENV YOSAI_ENV=production
EXPOSE 8050

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 CMD curl -f http://localhost:8050/ || exit 1

COPY start.sh ./start.sh
RUN chmod +x start.sh

CMD ["./start.sh"]
