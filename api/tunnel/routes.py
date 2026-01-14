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
from shared.utils.process import is_cloudflared_running, find_cloudflared_processes, kill_process
from shared.utils.tunnel import get_tunnel_hostname


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
                'message': 'Configuración de túnel no encontrada. Ejecutar: python setup_tunnel.py'
            }), 400

        # Leer y verificar el config.yml
        try:
            config_content = cloudflare_config.read_text()
            print(f"[TUNNEL-START] Config encontrado en: {cloudflare_config}")

            # Verificar que el archivo de credenciales existe
            import re
            credentials_match = re.search(r'credentials-file:\s*(.+)', config_content)
            if credentials_match:
                credentials_path = Path(credentials_match.group(1).strip())
                if not credentials_path.exists():
                    return jsonify({
                        'success': False,
                        'message': f'Archivo de credenciales no encontrado: {credentials_path}. Ejecutar: python setup_tunnel.py'
                    }), 400
                print(f"[TUNNEL-START] Credenciales encontradas en: {credentials_path}")
            else:
                return jsonify({
                    'success': False,
                    'message': 'Config inválido: falta credentials-file. Ejecutar: python setup_tunnel.py'
                }), 400
        except Exception as config_error:
            print(f"[TUNNEL-START] Error leyendo config: {config_error}")
            return jsonify({
                'success': False,
                'message': f'Error en configuración: {str(config_error)}'
            }), 400

        # Verificar si ya está corriendo (multiplataforma)
        if is_cloudflared_running():
            return jsonify({
                'success': False,
                'message': 'El túnel ya está activo'
            }), 400

        # Obtener configuración y determinar hostname del túnel
        config = get_config_data()
        hostname = get_tunnel_hostname(config)

        # Iniciar túnel en background
        # En Windows, necesitamos el path completo del ejecutable
        cloudflared_path = shutil.which('cloudflared')

        # Leer el tunnel ID del config.yml
        import re
        tunnel_id_match = re.search(r'tunnel:\s*([a-f0-9\-]+)', config_content)
        tunnel_id = tunnel_id_match.group(1) if tunnel_id_match else None

        # Comando: Si tenemos tunnel_id, usarlo; sino usar 'tunnel run' sin nombre
        # que usará el config.yml automáticamente
        if tunnel_id:
            cmd = [cloudflared_path, 'tunnel', 'run', tunnel_id]
            print(f"[TUNNEL-START] Iniciando cloudflared desde: {cloudflared_path}")
            print(f"[TUNNEL-START] Comando: {' '.join(cmd)}")
            print(f"[TUNNEL-START] Tunnel ID: {tunnel_id}")
        else:
            # Fallback: usar 'tunnel run' sin argumentos, lee config.yml automáticamente
            cmd = [cloudflared_path, 'tunnel', 'run']
            print(f"[TUNNEL-START] Iniciando cloudflared desde: {cloudflared_path}")
            print(f"[TUNNEL-START] Comando: {' '.join(cmd)} (usando config.yml)")

        # Capturar salida para debugging
        import tempfile
        import platform
        log_file = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.log')

        try:
            # En Windows, usar creationflags para iniciar proceso detached
            # Esto permite que el proceso continúe ejecutándose independientemente
            if platform.system() == 'Windows':
                # DETACHED_PROCESS = 0x00000008 - Proceso independiente
                # CREATE_NO_WINDOW = 0x08000000 - Sin ventana de consola visible
                # Nota: No usamos CREATE_NEW_PROCESS_GROUP porque puede causar que se muestre ventana
                DETACHED_PROCESS = 0x00000008
                CREATE_NO_WINDOW = 0x08000000
                creation_flags = DETACHED_PROCESS | CREATE_NO_WINDOW

                # Usar startupinfo para máxima ocultación
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0  # SW_HIDE = 0

                # Redirigir todo a DEVNULL para evitar pipes que puedan crear ventanas
                process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=creation_flags,
                    startupinfo=startupinfo,
                    shell=False
                )
            else:
                # Unix/Linux: usar start_new_session
                process = subprocess.Popen(
                    cmd,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    start_new_session=True
                )

            print(f"[TUNNEL-START] Proceso iniciado con PID: {process.pid}")

            # Esperar un momento para verificar que se inició
            time.sleep(5)

            # Leer logs si el proceso falló
            log_file.seek(0)
            log_content = log_file.read()
            log_file.close()

            # Verificar que se inició correctamente (multiplataforma)
            if is_cloudflared_running():
                print(f"[TUNNEL-START] ✅ Túnel iniciado correctamente")
                print(f"[TUNNEL-START] URL del túnel: https://{hostname}")
                return jsonify({
                    'success': True,
                    'message': f'Túnel iniciado correctamente',
                    'subdomain': hostname,
                    'url': f'https://{hostname}',
                    'pid': process.pid
                }), 200
            else:
                print(f"[TUNNEL-START] ❌ Túnel no está corriendo después de iniciar")
                print(f"[TUNNEL-START] Logs de cloudflared:\n{log_content}")

                return jsonify({
                    'success': False,
                    'message': f'Error al iniciar el túnel. Revisa la configuración en ~/.cloudflared/config.yml',
                    'details': log_content[:500] if log_content else 'Sin logs disponibles'
                }), 500
        except Exception as start_error:
            print(f"[TUNNEL-START] ❌ Excepción al iniciar: {start_error}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': f'Error al ejecutar cloudflared: {str(start_error)}'
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
        # Buscar procesos de cloudflared (multiplataforma)
        pids = find_cloudflared_processes()

        if not pids:
            return jsonify({
                'success': False,
                'message': 'No hay túneles activos'
            }), 400

        # Matar cada proceso (multiplataforma)
        for pid in pids:
            kill_process(pid)

        return jsonify({
            'success': True,
            'message': 'Túnel detenido correctamente'
        }), 200

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
        # Verificar si cloudflared está corriendo (multiplataforma)
        is_active = False
        pids = []

        try:
            is_active = is_cloudflared_running()
            if is_active:
                # Obtener PIDs (multiplataforma)
                pids = find_cloudflared_processes()
        except Exception as check_error:
            # Log el error pero no fallar - simplemente asumir que no está corriendo
            print(f"[TUNNEL-STATUS] Error verificando cloudflared: {check_error}")
            is_active = False
            pids = []

        # Obtener configuración y determinar hostname del túnel
        config = get_config_data()
        hostname = get_tunnel_hostname(config)

        response_data = {
            'success': True,
            'active': is_active,
            'subdomain': hostname,
            'url': f'https://{hostname}' if is_active else None,
            'machine_id': config.get('machine_id', '')
        }

        if is_active and pids:
            response_data['pids'] = [str(pid) for pid in pids]

        return jsonify(response_data), 200

    except Exception as e:
        # Log más detallado del error
        import traceback
        error_detail = traceback.format_exc()
        print(f"[TUNNEL-STATUS] Error crítico: {e}")
        print(f"[TUNNEL-STATUS] Traceback: {error_detail}")

        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500
