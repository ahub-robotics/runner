"""
Web UI Main Pages.

Provides main user interface pages:
    - GET /: Home page (redirects to connected or connect)
    - GET/POST /connect: Initial configuration page
    - GET/POST /connected: Main dashboard
"""
from flask import Blueprint, redirect, url_for, render_template, request
from api.auth import require_auth


# Create blueprint
web_ui_bp = Blueprint('web_ui', __name__)


def get_server():
    """Get server instance from api module."""
    from api import get_server
    return get_server()


@web_ui_bp.route('/', methods=['GET'])
@require_auth
def home():
    """
    GET / - Página de inicio.

    Requiere autenticación por token.

    Redirige a:
        - /connected: Si el servidor está configurado
        - /connect: Si necesita configuración inicial

    Returns:
        Redirect
    """
    server = get_server()
    
    try:
        if server:
            server.status = 'free'
        return redirect(url_for('web_ui.connected'))
    except Exception:
        return redirect(url_for('web_ui.connect'))


@web_ui_bp.route('/connect', methods=['GET', 'POST'])
@require_auth
def connect():
    """
    GET/POST /connect - Página de configuración inicial.

    GET:
        Muestra formulario de configuración

    POST:
        Guarda la configuración y redirige a /connected

    Returns:
        Renderiza form.html o redirect a /connected
        
    Note:
        Esta ruta será migrada completamente en un próximo paso.
        Por ahora es un placeholder que muestra el formulario básico.
    """
    if request.method == 'POST':
        # TODO: Implementar guardado de configuración
        return redirect(url_for('web_ui.connected'))
    
    return render_template('form.html')


@web_ui_bp.route('/connected', methods=['GET', 'POST'])
@require_auth
def connected():
    """
    GET/POST /connected - Dashboard principal.

    GET:
        Muestra el dashboard con información del servidor

    POST:
        Maneja desconexión del robot

    Returns:
        Renderiza connected.html o redirect según acción
        
    Note:
        Esta ruta será migrada completamente en un próximo paso.
        Por ahora es un placeholder básico.
    """
    server = get_server()
    
    if request.method == 'POST':
        # Handle disconnect
        return redirect(url_for('web_ui.connect'))
    
    # Render dashboard
    return render_template('connected.html', 
                          machine_id=server.machine_id if server else 'N/A',
                          status=server.status if server else 'unknown')
