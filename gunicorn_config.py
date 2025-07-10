# gunicorn_config.py
import multiprocessing

# Worker configuration - optimized for Render.com
worker_class = 'gevent'  # Use gevent for async I/O operations
workers = min(multiprocessing.cpu_count() * 2 + 1, 3)  # Max 3 workers for memory efficiency
threads = 2

# Timeouts
timeout = 300  # 5 minutes
graceful_timeout = 30

# Memory management
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = 'access.log'
errorlog = 'error.log'
loglevel = 'info'
