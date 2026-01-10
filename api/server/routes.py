"""
Server Management Endpoints.

Provides server control:
    - POST /server/restart: Restart Flask/Gunicorn/Waitress server
"""
import os
import sys
import time
import signal
import platform
import threading
from flask import Blueprint, jsonify
from api.auth import require_auth


# Create blueprint
server_mgmt_bp = Blueprint('server_mgmt', __name__, url_prefix='/server')


@server_mgmt_bp.route('/restart', methods=['POST'])
@require_auth
def restart_server():
    """
    POST /server/restart - Reinicia el servidor Flask/Gunicorn/Waitress.

    Este endpoint programa el reinicio del servidor después de enviar la respuesta.

    Comportamiento multiplataforma:
    - Linux/macOS con Gunicorn: Envía SIGHUP para reinicio graceful de workers
    - Windows con Waitress: Envía SIGTERM para terminar el proceso (se reinicia automáticamente)
    - Fallback: sys.exit() si las señales no están disponibles

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

            system = platform.system()

            if system == 'Windows':
                # Windows: usar SIGTERM (Waitress terminará y el supervisor lo reiniciará)
                # SIGHUP no existe en Windows
                if hasattr(signal, 'SIGTERM'):
                    print("[SERVER-RESTART] Enviando SIGTERM en Windows...")
                    os.kill(os.getpid(), signal.SIGTERM)
                else:
                    print("[SERVER-RESTART] Fallback: usando sys.exit()...")
                    sys.exit(0)
            else:
                # Linux/macOS: usar SIGHUP para reinicio graceful de Gunicorn
                if hasattr(signal, 'SIGHUP'):
                    print("[SERVER-RESTART] Enviando SIGHUP en Unix...")
                    os.kill(os.getpid(), signal.SIGHUP)
                elif hasattr(signal, 'SIGTERM'):
                    print("[SERVER-RESTART] Fallback: usando SIGTERM...")
                    os.kill(os.getpid(), signal.SIGTERM)
                else:
                    print("[SERVER-RESTART] Fallback: usando sys.exit()...")
                    sys.exit(0)

        # Programar el reinicio en background
        threading.Thread(target=trigger_restart, daemon=True, name='ServerRestartThread').start()

        return jsonify({
            'success': True,
            'message': 'Servidor reiniciándose...'
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al reiniciar: {str(e)}'
        }), 500
