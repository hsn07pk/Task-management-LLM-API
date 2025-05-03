FROM python:3.9-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

FROM python:3.9-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    supervisor \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtualenv from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Create directories for logs with appropriate permissions
RUN mkdir -p /var/log/gunicorn /var/log/supervisor

# Copy supervisor configuration
COPY deployment/supervisor/task_management_api.conf /etc/supervisor/conf.d/

# Copy gunicorn configuration
COPY deployment/gunicorn/gunicorn.conf.py /app/deployment/gunicorn/
COPY deployment/gunicorn/start.sh /app/deployment/gunicorn/

# Copy application code
COPY . .

# Ensure script is executable and permissions are set correctly
RUN chmod +x /app/deployment/gunicorn/start.sh && \
    chmod -R 755 /var/log/gunicorn /var/log/supervisor && \
    mkdir -p /app/static

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/health || exit 1

# Start supervisor (which will start Gunicorn)
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf", "-n"]
