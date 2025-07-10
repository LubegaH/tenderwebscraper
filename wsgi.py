"""
WSGI entry point for production deployment.
Properly handles gevent monkey patching before any SSL imports.
"""
import os

# Apply gevent monkey patching BEFORE any other imports
if os.environ.get('FLASK_ENV') != 'development':
    # Only patch in production to avoid SSL recursion issues
    import gevent.monkey
    gevent.monkey.patch_all()

# Now import the Flask app
from app import app

# Export for gunicorn
application = app

if __name__ == "__main__":
    application.run()