"""
Web UI Settings Page.

Provides configuration management:
    - GET/POST /settings: Server configuration with tunnel management
"""
import os
import subprocess
import time
import threading
import signal
from pathlib import Path
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from api import get_server, set_server
from api.auth import require_auth
from shared.config.loader import get_config_data, save_config_data
from shared.utils.process import is_cloudflared_running, find_cloudflared_processes, kill_process


# Create blueprint
web_settings_bp = Blueprint('web_settings', __name__)


@web_settings_bp.route('/settings', methods=['GET', 'POST'])
@require_auth
def settings():
    """
    GET/POST /settings - Página de configuración del servidor.

    GET: Muestra el formulario de configuración con los valores actuales
    POST: Guarda la nueva configuración en config.json

    Form Fields (POST):
        - url: URL del orquestador
        - token: Token de autenticación
        - machine_id: ID de la máquina
        - license_key: License key
        - ip: IP pública
        - port: Puerto del servidor (cambiar requiere reinicio)
        - tunnel_subdomain: Subdominio de Cloudflare
        - tunnel_id: ID del tunnel de Cloudflare

    Returns:
        GET: HTML con formulario de configuración
        POST: Redirect a /settings o JSON si cambió puerto

    Side Effects:
        - Actualiza config.json
        - Reconfigura Cloudflare tunnel si cambió subdominio/puerto
        - Reinicia tunnel si estaba activo
        - Reinicia servidor si cambió puerto (con delay)
    """
    if request.method == 'POST':
        try:
            # Obtener configuración actual para comparar cambios
            old_config = get_config_data()
            old_subdomain = old_config.get('tunnel_subdomain', '').strip()
            if not old_subdomain:
                old_subdomain = old_config.get('machine_id', '').strip()
            old_port = str(old_config.get('port', '5055'))

            # Obtener datos del formulario
            new_config = {
                'url': request.form.get('url', ''),
                'token': request.form.get('token', ''),
                'machine_id': request.form.get('machine_id', ''),
                'license_key': request.form.get('license_key', ''),
                'ip': request.form.get('ip', '0.0.0.0'),
                'port': request.form.get('port', '5055'),
                'tunnel_subdomain': request.form.get('tunnel_subdomain', ''),
                'tunnel_id': request.form.get('tunnel_id', '3d7de42c-4a8a-4447-b14f-053cc485ce6b')
            }

            # Determinar nuevo subdominio
            new_subdomain = new_config.get('tunnel_subdomain', '').strip()
            if not new_subdomain:
                new_subdomain = new_config.get('machine_id', '').strip()
            new_port = str(new_config.get('port', '5055'))

            # Verificar si cambió el subdominio o el puerto
            subdomain_changed = old_subdomain.lower() != new_subdomain.lower()
            port_changed = old_port != new_port
            tunnel_config_changed = subdomain_changed or port_changed

            # Verificar si el túnel está activo antes de hacer cambios (multiplataforma)
            tunnel_was_active = False
            if tunnel_config_changed:
                tunnel_was_active = is_cloudflared_running()

                # Si el túnel está activo, detenerlo primero
                if tunnel_was_active:
                    pids = find_cloudflared_processes()
                    for pid in pids:
                        kill_process(pid)
                    time.sleep(1)  # Esperar a que se detenga

            # Guardar configuración
            save_config_data(new_config)

            # Actualizar configuración de Cloudflare
            hostname = f"{new_subdomain.lower()}.automatehub.es"

            # Actualizar archivo de configuración de Cloudflare
            cloudflare_config_path = Path.home() / '.cloudflared' / 'config.yml'
            tunnel_id = new_config.get('tunnel_id', '3d7de42c-4a8a-4447-b14f-053cc485ce6b')
            credentials_path = Path.home() / '.cloudflared' / f'{tunnel_id}.json'

            config_content = f"""tunnel: {tunnel_id}
credentials-file: {credentials_path}

ingress:
  # Subdominio configurado: {hostname}
  - hostname: {hostname}
    service: https://localhost:{new_port}
    originRequest:
      noTLSVerify: true
  - service: http_status:404
"""

            cloudflare_config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(cloudflare_config_path, 'w') as f:
                f.write(config_content)

            # Crear ruta DNS en Cloudflare
            subprocess.run(
                ['cloudflared', 'tunnel', 'route', 'dns', 'robotrunner', hostname],
                capture_output=True,
                text=True
            )

            # Si el túnel estaba activo, reiniciarlo con la nueva configuración
            if tunnel_was_active:
                # En Windows, necesitamos el path completo del ejecutable
                import shutil
                cloudflared_path = shutil.which('cloudflared')
                if cloudflared_path:
                    subprocess.Popen(
                        [cloudflared_path, 'tunnel', 'run', 'robotrunner'],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True
                    )
                    time.sleep(2)  # Esperar a que se inicie

            # Actualizar el servidor global con la nueva configuración
            from executors.server import Server
            config_data = get_config_data()
            new_server = Server(config_data)
            set_server(new_server)

            # Si cambió el puerto, programar reinicio del servidor
            if port_changed:
                def trigger_restart_with_new_port():
                    time.sleep(1)
                    os.kill(os.getpid(), signal.SIGHUP)

                # Usar threading para tarea simple de restart
                threading.Thread(target=trigger_restart_with_new_port, daemon=True).start()

                # Retornar respuesta JSON con el nuevo puerto para que el frontend redirija
                return jsonify({
                    'success': True,
                    'port_changed': True,
                    'new_port': new_port,
                    'message': f'Configuración guardada. Reiniciando servidor en puerto {new_port}...'
                }), 200

            # Mensaje apropiado según lo que pasó
            if tunnel_config_changed and tunnel_was_active:
                flash(f'Configuración guardada y túnel reiniciado con nuevo subdominio: {hostname}', 'success')
            elif tunnel_config_changed:
                flash(f'Configuración guardada. Nuevo subdominio: {hostname}. Inicia el túnel para aplicar cambios.', 'success')
            else:
                flash('Configuración guardada correctamente.', 'success')

            return redirect(url_for('web_settings.settings'))

        except Exception as e:
            flash(f'Error al guardar configuración: {str(e)}', 'danger')
            return redirect(url_for('web_settings.settings'))

    # GET: Mostrar formulario con valores actuales
    config = get_config_data()
    return render_template('settings.html', config=config)
