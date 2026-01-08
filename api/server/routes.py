"""
Server Management Endpoints.

Provides server control:
    - POST /server/restart: Restart Flask/Gunicorn server
"""
import os
import time
import signal
import threading
from flask import Blueprint, jsonify
from api.auth import require_auth


# Create blueprint
server_bp = Blueprint('server', __name__, url_prefix='/server')


@server_bp.route('/restart', methods=['POST'])
@require_auth
def restart_server():
    """
    POST /server/restart - Reinicia el servidor Flask/Gunicorn.

    Este endpoint programa el reinicio del servidor después de enviar la respuesta.
    Nota: Solo funciona cuando se ejecuta con Gunicorn.

    Returns:
        JSON: Confirmación del reinicio programado

    Example Response:
        {
            "success": true,
            "message": "Servidor reiniciándose..."
        }
    """
    try:
        def trigger_restart():
            """Función que se ejecutará después de enviar la respuesta."""
            time.sleep(1)  # Esperar a que se envíe la respuesta
            # Enviar señal HUP a Gunicorn para reiniciar los workers
            os.kill(os.getpid(), signal.SIGHUP)

        # Programar el reinicio en background (usando threading ya que es una tarea simple)
        threading.Thread(target=trigger_restart, daemon=True).start()

        return jsonify({
            'success': True,
            'message': 'Servidor reiniciándose...'
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al reiniciar: {str(e)}'
        }), 500
