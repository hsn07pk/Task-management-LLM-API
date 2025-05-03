#!/bin/bash
set -e

# Set environment variables
export PYTHONPATH=/app
export FLASK_APP=app.py
export FLASK_ENV=production

# Create log directory with proper permissions
mkdir -p /var/log/gunicorn
chmod -R 755 /var/log/gunicorn

# Start Gunicorn
echo "Starting Gunicorn server..."
exec gunicorn --config /app/deployment/gunicorn/gunicorn.conf.py --chdir /app "app:create_app()"
