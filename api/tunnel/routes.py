"""
Tunnel Management Endpoints.

Provides Cloudflare tunnel management:
    - POST /tunnel/start: Start Cloudflare tunnel
    - POST /tunnel/stop: Stop Cloudflare tunnel
    - GET /tunnel/status: Get tunnel status
"""
import time
import shutil
import subprocess
from pathlib import Path
from flask import Blueprint, jsonify
from api.auth import require_auth
from shared.config.loader import get_config_data


# Create blueprint
tunnel_bp = Blueprint('tunnel', __name__, url_prefix='/tunnel')


@tunnel_bp.route('/start', methods=['POST'])
@require_auth
def start_tunnel():
    """
    POST /tunnel/start - Inicia el túnel de Cloudflare en background.

    Returns:
        JSON: Estado de la operación

    Example Response:
        {
            "success": true,
            "message": "Túnel iniciado correctamente",
            "subdomain": "robot-1.automatehub.es",
            "url": "https://robot-1.automatehub.es"
        }
    """
    try:
        # Verificar si cloudflared está instalado
        if not shutil.which('cloudflared'):
            return jsonify({
                'success': False,
                'message': 'cloudflared no está instalado. Instalar con: brew install cloudflared'
            }), 400

        # Verificar configuración
        cloudflare_config = Path.home() / '.cloudflared' / 'config.yml'
        if not cloudflare_config.exists():
            return jsonify({
                'success': False,
                'message': 'Configuración de túnel no encontrada. Ejecutar setup_machine_tunnel.py primero.'
            }), 400

        # Verificar si ya está corriendo
        result = subprocess.run(
            ['pgrep', '-f', 'cloudflared tunnel run'],
            capture_output=True,
            text=True
        )

        if result.stdout.strip():
            return jsonify({
                'success': False,
                'message': 'El túnel ya está activo'
            }), 400

        # Obtener configuración y determinar subdominio
        config = get_config_data()

        # Usar tunnel_subdomain si está configurado, si no usar machine_id
        subdomain_base = config.get('tunnel_subdomain', '').strip()
        if not subdomain_base:
            subdomain_base = config.get('machine_id', '').strip()

        subdomain = f"{subdomain_base.lower()}.automatehub.es" if subdomain_base else 'N/A'

        # Iniciar túnel en background
        subprocess.Popen(
            ['cloudflared', 'tunnel', 'run', 'robotrunner'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

        # Esperar un momento para verificar que se inició
        time.sleep(2)

        # Verificar que se inició correctamente
        result = subprocess.run(
            ['pgrep', '-f', 'cloudflared tunnel run'],
            capture_output=True,
            text=True
        )

        if result.stdout.strip():
            return jsonify({
                'success': True,
                'message': f'Túnel iniciado correctamente',
                'subdomain': subdomain,
                'url': f'https://{subdomain}'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Error al iniciar el túnel'
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@tunnel_bp.route('/stop', methods=['POST'])
@require_auth
def stop_tunnel():
    """
    POST /tunnel/stop - Detiene el túnel de Cloudflare.

    Returns:
        JSON: Estado de la operación

    Example Response:
        {
            "success": true,
            "message": "Túnel detenido correctamente"
        }
    """
    try:
        # Buscar procesos de cloudflared
        result = subprocess.run(
            ['pgrep', '-f', 'cloudflared tunnel run'],
            capture_output=True,
            text=True
        )

        if not result.stdout.strip():
            return jsonify({
                'success': False,
                'message': 'No hay túneles activos'
            }), 400

        # Obtener los PIDs
        pids = result.stdout.strip().split('\n')

        # Matar cada proceso
        for pid in pids:
            if pid:
                subprocess.run(['kill', pid], check=True)

        return jsonify({
            'success': True,
            'message': 'Túnel detenido correctamente'
        }), 200

    except subprocess.CalledProcessError as e:
        return jsonify({
            'success': False,
            'message': f'Error al detener el túnel: {str(e)}'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@tunnel_bp.route('/status', methods=['GET'])
@require_auth
def tunnel_status():
    """
    GET /tunnel/status - Obtiene el estado del túnel de Cloudflare.

    Returns:
        JSON: Estado del túnel (active/inactive) y detalles

    Example Response:
        {
            "success": true,
            "active": true,
            "subdomain": "robot-1.automatehub.es",
            "url": "https://robot-1.automatehub.es",
            "machine_id": "robot-1",
            "pids": ["12345"]
        }
    """
    try:
        # Verificar si cloudflared está corriendo
        result = subprocess.run(
            ['pgrep', '-f', 'cloudflared tunnel run'],
            capture_output=True,
            text=True
        )

        is_active = bool(result.stdout.strip())

        # Obtener configuración y determinar subdominio
        config = get_config_data()

        # Usar tunnel_subdomain si está configurado, si no usar machine_id
        subdomain_base = config.get('tunnel_subdomain', '').strip()
        if not subdomain_base:
            subdomain_base = config.get('machine_id', '').strip()

        subdomain = f"{subdomain_base.lower()}.automatehub.es" if subdomain_base else 'N/A'

        response_data = {
            'success': True,
            'active': is_active,
            'subdomain': subdomain,
            'url': f'https://{subdomain}' if is_active else None,
            'machine_id': config.get('machine_id', '')
        }

        if is_active:
            # Obtener PIDs
            pids = result.stdout.strip().split('\n')
            response_data['pids'] = pids

        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500
