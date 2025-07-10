#!/usr/bin/env python3
"""
Development server startup script - finds an available port and starts the server.
"""
import os
import socket
from app import app

def find_available_port(start_port=5000):
    """Find an available port starting from start_port."""
    for port in range(start_port, start_port + 100):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('localhost', port))
            sock.close()
            return port
        except OSError:
            continue
    raise RuntimeError("No available ports found")

if __name__ == '__main__':
    try:
        port = find_available_port(5000)
        print(f"🚀 Starting SHA Website Crawler on port {port}")
        print(f"📱 Visit: http://localhost:{port}")
        print("🔧 Debug mode enabled")
        print("🛑 Press Ctrl+C to stop the server")
        print("-" * 50)
        
        app.run(debug=True, host='0.0.0.0', port=port)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")