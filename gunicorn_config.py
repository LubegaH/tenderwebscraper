# gunicorn_config.py
import multiprocessing
import os

# Worker configuration - optimized for Render.com
# Use sync workers to avoid gevent SSL issues in production
worker_class = 'sync' if os.environ.get('FLASK_ENV') != 'development' else 'gevent'
workers = min(multiprocessing.cpu_count() + 1, 2)  # Max 2 workers for memory efficiency
threads = 1  # Keep threads low for memory

# Reduced timeouts for faster failure detection
timeout = 120  # 2 minutes instead of 5
graceful_timeout = 30

# Memory management - more aggressive recycling
max_requests = 500  # Recycle workers more frequently
max_requests_jitter = 25

# Logging
accesslog = 'access.log'
errorlog = 'error.log'
loglevel = 'info'

# Additional settings for stability
preload_app = True  # Load app before forking workers
bind = f"0.0.0.0:{os.environ.get('PORT', 8000)}"
