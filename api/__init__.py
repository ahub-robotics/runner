"""
API module for Robot Runner.

This module provides the Flask application factory and all API/web endpoints
organized into specialized submodules:
    - web: User-facing web interface
    - rest: REST API for robot control
    - streaming: Video streaming endpoints
    - tunnel: Cloudflare tunnel management
    - server: Server management
"""

# Global server instance (initialized lazily in middleware)
_server = None


def get_server():
    """
    Get the global server instance.
    
    Returns:
        Server instance or None if not yet initialized
    """
    return _server


def set_server(server):
    """
    Set the global server instance.
    
    Args:
        server: Server instance to set
    """
    global _server
    _server = server
