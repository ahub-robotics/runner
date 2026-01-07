"""
WSGI Entry Point for Gunicorn.

This module provides the WSGI application object that Gunicorn uses
to run the Flask application.

Usage:
    gunicorn api.wsgi:app --config gunicorn_config.py
    
    Or with custom options:
    gunicorn api.wsgi:app \\
        --bind 0.0.0.0:5001 \\
        --workers 1 \\
        --threads 4 \\
        --certfile ssl/cert.pem \\
        --keyfile ssl/key.pem
"""
from .app import create_app

# Create Flask application instance
app = create_app()

# For development/debugging
if __name__ == '__main__':
    # This should not be used in production
    # Use gunicorn instead: gunicorn api.wsgi:app
    print("[WARNING] Running Flask development server. Use Gunicorn for production!")
    app.run(debug=True, host='0.0.0.0', port=5000)
