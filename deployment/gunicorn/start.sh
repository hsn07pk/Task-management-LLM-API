#!/bin/bash

# Activate virtual environment if applicable
# source /path/to/venv/bin/activate

# Set environment variables
export PYTHONPATH=/app
export FLASK_APP=app.py
export FLASK_ENV=production

# Create log directory
mkdir -p /var/log/gunicorn

# Start Gunicorn
exec gunicorn --config /app/deployment/gunicorn/gunicorn.conf.py --chdir /app "app:create_app()"