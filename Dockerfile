FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
      supervisor \
      && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Create directories for logs
RUN mkdir -p /var/log/gunicorn /var/log/supervisor

# Copy supervisor configuration
COPY deployment/supervisor/task_management_api.conf /etc/supervisor/conf.d/

# Copy start script and make it executable
COPY deployment/gunicorn/start.sh /app/deployment/gunicorn/start.sh
RUN chmod +x /app/deployment/gunicorn/start.sh

# Copy application code
COPY . .

# Create .env file
RUN echo "FLASK_APP=app.py" > .env
RUN echo "FLASK_ENV=production" >> .env
RUN echo "SQLALCHEMY_DATABASE_URI=postgresql://admin:helloworld123@postgres:5432/task_management_db" >> .env
RUN echo "JWT_SECRET_KEY=your_secure_jwt_key_here" >> .env

# Start supervisor (which will start Gunicorn)
CMD ["/usr/bin/supervisord", "-n"]