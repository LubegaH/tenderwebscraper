#!/usr/bin/env python3
import os
import platform
import subprocess

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    
    # Default to development mode for local testing
    flask_env = os.environ.get('FLASK_ENV', 'development')
    
    if flask_env == 'development':
        print(f"🚀 Starting development server on port {port}")
        print("🔧 Debug mode enabled")
        from app import app
        app.run(debug=True, host='0.0.0.0', port=port)
    else:
        print(f"🚀 Starting production server on port {port}")
        # Use appropriate production server based on platform
        if platform.system() == 'Windows':
            from waitress import serve
            from app import app
            serve(app, host='0.0.0.0', port=port)
        else:
            # Use gunicorn with config file
            subprocess.run([
                'gunicorn',
                '--config=gunicorn_config.py',
                '-b', f'0.0.0.0:{port}',
                'app:app'
            ])
