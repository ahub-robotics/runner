"""
Web UI Main Pages.

Provides main user interface pages:
    - GET /: Home page (redirects to connected or connect)
    - GET/POST /connect: Initial configuration page
    - GET/POST /connected: Main dashboard
"""
import os
from flask import Blueprint, redirect, url_for, render_template, request
from api.auth import require_auth
from shared.config.loader import get_config_data, write_to_config


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
    /connect - Página de configuración inicial.

    Requiere autenticación por token.

    GET:
        Muestra formulario de configuración con los valores actuales
        del config.json.

    POST:
        Guarda la configuración proporcionada y redirige a /connected.

    Form Fields:
        - ip: IP pública del robot
        - port: Puerto del servidor
        - token: Token de autenticación del orquestador
        - machine_id: ID único de la máquina
        - license_key: License key de la máquina
        - url: URL del orquestador/consola

    Returns:
        GET: Renderiza form.html
        POST: Redirect a /home
    """
    server = get_server()

    if request.method == "GET":
        config_data = get_config_data()
        message = "Set machine credentials from the Robot Console."

        return render_template(
            'form.html',
            ip=config_data.get("ip", os.popen('curl -s ifconfig.me').readline()),
            port=config_data["port"],
            token=config_data["token"],
            machine_id=config_data["machine_id"],
            license_key=config_data["license_key"],
            url=config_data["url"],
            message=message,
            color="white"
        )

    elif request.method == "POST":
        data = request.form

        if server:
            # Actualizar configuración del servidor
            server.url = server.clean_url(data['url'])
            server.token = data['token']
            server.machine_id = data['machine_id']
            server.license_key = data['license_key']

        try:
            if server:
                # Establecer estado como 'free' y notificar al servidor remoto
                server.change_status('free', notify_remote=True)

            # Guardar configuración
            write_to_config(data)

            return redirect(url_for("web_ui.home"))

        except Exception:
            config_data = get_config_data()
            message = "Invalid credentials, check them in the console and try again."

            return render_template(
                'form.html',
                ip=config_data["ip"],
                port=config_data["port"],
                token=config_data["token"],
                machine_id=config_data["machine_id"],
                license_key=config_data["license_key"],
                url=config_data["url"],
                message=message,
                color="red"
            )


@web_ui_bp.route('/connected', methods=['GET', 'POST'])
@require_auth
def connected():
    """
    /connected - Página principal cuando el robot está conectado.

    Requiere autenticación por token.

    GET:
        Muestra el dashboard del robot con su estado actual.

    POST:
        Desconecta el robot y redirige a /connect.

    Returns:
        GET: Renderiza connected.html
        POST: Redirect a /connect
    """
    server = get_server()

    if request.method == 'GET':
        # Pasar datos del servidor al template
        if server:
            server_data = {
                'status': server.status,
                'machine_id': server.machine_id,
                'license_key': server.license_key,
                'token': server.token,
                'url': server.url,
                'ip': server.ip,
                'port': server.port
            }
        else:
            server_data = {
                'status': 'unknown',
                'machine_id': 'N/A',
                'license_key': 'N/A',
                'token': 'N/A',
                'url': 'N/A',
                'ip': 'N/A',
                'port': 'N/A'
            }
        return render_template('connected.html', server=server_data)

    elif request.method == "POST":
        if server:
            server.stop_execution()
            server.change_status('closed', notify_remote=True)
        return redirect(url_for("web_ui.connect"))
