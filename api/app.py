"""
Flask Application Factory for Robot Runner.

Creates and configures the Flask application with all routes, middleware,
and blueprints registered.
"""
import os
import secrets
import warnings
from datetime import timedelta
from pathlib import Path

import flask
from flask import Flask
from urllib3.exceptions import InsecureRequestWarning

from .middleware import register_middleware


# Suprimir warnings de SSL para peticiones internas
warnings.filterwarnings('ignore', category=InsecureRequestWarning)

# Directorio raíz del proyecto (dos niveles arriba de api/)
PROJECT_ROOT = Path(__file__).parent.parent.absolute()


def create_app(config=None):
    """
    Flask application factory.
    
    Creates and configures a Flask application instance with:
    - Template and static folder configuration
    - Session management (30-day lifetime, secure cookies)
    - File upload limits
    - Middleware (logging, authentication)
    - Blueprints (web UI, REST API, streaming, tunnel, server management)
    
    Args:
        config (dict, optional): Additional configuration to override defaults
        
    Returns:
        Flask: Configured Flask application instance
        
    Example:
        >>> app = create_app()
        >>> app.run(debug=True)
    """
    # Crear aplicación Flask con rutas correctas para templates y static
    app = Flask(
        __name__,
        template_folder=str(PROJECT_ROOT / 'templates'),
        static_folder=str(PROJECT_ROOT / 'static')
    )
    
    # Configuración de Flask
    configure_flask(app, config)
    
    # Registrar middleware (logging, server init, etc.)
    register_middleware(app)
    
    # Registrar blueprints (rutas organizadas por funcionalidad)
    register_blueprints(app)
    
    print("[APP-FACTORY] ✅ Flask app creada y configurada")
    
    return app


def configure_flask(app, config=None):
    """
    Configure Flask application settings.
    
    Sets up:
    - Upload folder and file size limits
    - Secret key for sessions
    - Secure cookie settings (HTTPS-only, HttpOnly, SameSite)
    - Session lifetime (30 days permanent sessions)
    
    Args:
        app (Flask): Flask application instance
        config (dict, optional): Additional configuration to merge
    """
    # Configuración base
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Límite: 16 MB
    
    # Secret key para sesiones (desde env o generado)
    app.config['SECRET_KEY'] = os.environ.get(
        'FLASK_SECRET_KEY',
        secrets.token_hex(32)
    )

    # Detectar si SSL está configurado
    ssl_folder = Path.home() / 'Robot' / 'ssl'
    has_ssl = (ssl_folder / 'cert.pem').exists() and (ssl_folder / 'key.pem').exists()

    # Configuración de cookies seguras
    # IMPORTANTE: SESSION_COOKIE_SECURE solo funciona con HTTPS
    # Si no hay SSL, debe ser False para que funcione con HTTP
    app.config['SESSION_COOKIE_SECURE'] = has_ssl  # True si hay SSL, False si no
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # No accesible desde JavaScript
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Protección CSRF
    
    # Configuración de sesiones permanentes (30 días)
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
    
    # Merge custom config if provided
    if config:
        app.config.update(config)
    
    print("[CONFIG] Flask configurado: upload_folder, sessions, security")


def register_blueprints(app):
    """
    Register all Flask blueprints with the application.
    
    Blueprints organize routes by functionality:
    - web_auth: Login/logout
    - web_ui: Main UI pages
    - web_settings: Configuration page
    - rest_api: Robot control endpoints
    - streaming: Video streaming
    - tunnel: Cloudflare tunnel management
    - server_mgmt: Server restart
    
    Args:
        app (Flask): Flask application instance
        
    Note:
        Blueprints are registered when they exist. During incremental
        migration, some blueprints may not be available yet.
    """
    print("[BLUEPRINTS] Registrando blueprints...")
    
    # WEB UI BLUEPRINTS
    try:
        from .web.auth import web_auth_bp
        app.register_blueprint(web_auth_bp)
        print("[BLUEPRINTS] ✅ web_auth registrado")
    except ImportError:
        print("[BLUEPRINTS] ⚠️  web_auth no disponible (pendiente migración)")
    
    try:
        from .web.ui import web_ui_bp
        app.register_blueprint(web_ui_bp)
        print("[BLUEPRINTS] ✅ web_ui registrado")
    except ImportError:
        print("[BLUEPRINTS] ⚠️  web_ui no disponible (pendiente migración)")
    
    try:
        from .web.settings import web_settings_bp
        app.register_blueprint(web_settings_bp)
        print("[BLUEPRINTS] ✅ web_settings registrado")
    except ImportError:
        print("[BLUEPRINTS] ⚠️  web_settings no disponible (pendiente migración)")
    
    # REST API BLUEPRINTS
    try:
        from .rest.status import rest_status_bp
        app.register_blueprint(rest_status_bp)
        print("[BLUEPRINTS] ✅ rest_status registrado")
    except ImportError:
        print("[BLUEPRINTS] ⚠️  rest_status no disponible (pendiente migración)")
    
    try:
        from .rest.execution import rest_execution_bp
        app.register_blueprint(rest_execution_bp)
        print("[BLUEPRINTS] ✅ rest_execution registrado")
    except ImportError:
        print("[BLUEPRINTS] ⚠️  rest_execution no disponible (pendiente migración)")
    
    try:
        from .rest.info import rest_info_bp
        app.register_blueprint(rest_info_bp)
        print("[BLUEPRINTS] ✅ rest_info registrado")
    except ImportError:
        print("[BLUEPRINTS] ⚠️  rest_info no disponible (pendiente migración)")
    
    # STREAMING BLUEPRINTS
    try:
        from .streaming.control import streaming_control_bp
        app.register_blueprint(streaming_control_bp)
        print("[BLUEPRINTS] ✅ streaming_control registrado")
    except ImportError:
        print("[BLUEPRINTS] ⚠️  streaming_control no disponible (pendiente migración)")
    
    try:
        from .streaming.feed import streaming_feed_bp
        app.register_blueprint(streaming_feed_bp)
        print("[BLUEPRINTS] ✅ streaming_feed registrado")
    except ImportError:
        print("[BLUEPRINTS] ⚠️  streaming_feed no disponible (pendiente migración)")
    
    # TUNNEL BLUEPRINTS
    try:
        from .tunnel.routes import tunnel_bp
        app.register_blueprint(tunnel_bp)
        print("[BLUEPRINTS] ✅ tunnel registrado")
    except ImportError:
        print("[BLUEPRINTS] ⚠️  tunnel no disponible (pendiente migración)")
    
    # SERVER MANAGEMENT BLUEPRINTS
    try:
        from .server.routes import server_mgmt_bp
        app.register_blueprint(server_mgmt_bp)
        print("[BLUEPRINTS] ✅ server_mgmt registrado")
    except ImportError:
        print("[BLUEPRINTS] ⚠️  server_mgmt no disponible (pendiente migración)")
    
    print("[BLUEPRINTS] Registro de blueprints completado")


# Para desarrollo/testing directo
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
