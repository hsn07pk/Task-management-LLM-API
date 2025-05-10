# Gunicorn configuration
import multiprocessing

# Bind address
bind = "0.0.0.0:8000"

# Number of worker processes
workers = multiprocessing.cpu_count() * 2 + 1

# Worker type
worker_class = "sync"

# Timeouts
timeout = 120
keepalive = 5

# Log settings
errorlog = "/var/log/gunicorn/error.log"
accesslog = "/var/log/gunicorn/access.log"
loglevel = "info"

# Process naming
proc_name = "task_management_api"

# Limit the number of requests
max_requests = 1000
max_requests_jitter = 50
