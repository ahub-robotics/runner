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
from shared.utils.tunnel import get_tunnel_hostname


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
            old_hostname = get_tunnel_hostname(old_config)
            old_port = str(old_config.get('port', '5055'))

            # Obtener datos del formulario
            # IMPORTANTE: NO usar tunnel_id hardcoded por defecto, usar el del config actual
            new_config = {
                'url': request.form.get('url', ''),
                'token': request.form.get('token', ''),
                'machine_id': request.form.get('machine_id', ''),
                'license_key': request.form.get('license_key', ''),
                'ip': request.form.get('ip', '0.0.0.0'),
                'port': request.form.get('port', '5055'),
                'tunnel_subdomain': request.form.get('tunnel_subdomain', ''),
                'tunnel_id': request.form.get('tunnel_id', old_config.get('tunnel_id', ''))
            }

            print(f"[SETTINGS] Configuración recibida del formulario:")
            print(f"  - tunnel_subdomain: '{new_config['tunnel_subdomain']}'")
            print(f"  - tunnel_id: '{new_config['tunnel_id']}'")
            print(f"  - port: '{new_config['port']}'")

            # Determinar nuevo hostname del túnel
            new_hostname = get_tunnel_hostname(new_config)
            new_port = str(new_config.get('port', '5055'))

            print(f"[SETTINGS] Hostname calculado: '{new_hostname}' (anterior: '{old_hostname}')")

            # Verificar si cambió el hostname o el puerto
            hostname_changed = old_hostname.lower() != new_hostname.lower()
            port_changed = old_port != new_port
            tunnel_config_changed = hostname_changed or port_changed

            print(f"[SETTINGS] ¿Cambió hostname? {hostname_changed}, ¿Cambió puerto? {port_changed}")

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

            # Usar el hostname ya calculado
            hostname = new_hostname

            # Actualizar archivo de configuración de Cloudflare
            cloudflare_config_path = Path.home() / '.cloudflared' / 'config.yml'
            # IMPORTANTE: NO usar tunnel_id hardcoded por defecto
            tunnel_id = new_config.get('tunnel_id', '')
            if not tunnel_id:
                raise ValueError("tunnel_id no configurado en el formulario")
            credentials_path = Path.home() / '.cloudflared' / f'{tunnel_id}.json'

            # Detectar si el servidor tiene SSL configurado
            ssl_folder = Path.home() / 'Robot' / 'ssl'
            has_ssl = (ssl_folder / 'cert.pem').exists() and (ssl_folder / 'key.pem').exists()
            service_protocol = 'https' if has_ssl else 'http'

            config_content = f"""tunnel: {tunnel_id}
credentials-file: {credentials_path}

ingress:
  # Subdominio configurado: {hostname}
  - hostname: {hostname}
    service: {service_protocol}://localhost:{new_port}"""

            # Si usa HTTPS, añadir noTLSVerify
            if has_ssl:
                config_content += """
    originRequest:
      noTLSVerify: true"""

            config_content += """
  - service: http_status:404
"""

            cloudflare_config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(cloudflare_config_path, 'w') as f:
                f.write(config_content)

            print(f"[SETTINGS] ✅ Config.yml actualizado con hostname: {hostname}")

            # Crear ruta DNS en Cloudflare usando tunnel_id
            try:
                result = subprocess.run(
                    ['cloudflared', 'tunnel', 'route', 'dns', tunnel_id, hostname],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    print(f"[SETTINGS] ✅ Ruta DNS creada: {hostname} -> {tunnel_id}")
                else:
                    # No es crítico si falla, puede ser que ya exista la ruta
                    print(f"[SETTINGS] ⚠️  Advertencia al crear ruta DNS: {result.stderr}")
            except Exception as dns_error:
                # No es crítico, continuar
                print(f"[SETTINGS] ⚠️  No se pudo crear ruta DNS: {dns_error}")

            # Si el túnel estaba activo, reiniciarlo con la nueva configuración
            if tunnel_was_active:
                # En Windows, necesitamos el path completo del ejecutable
                import shutil
                import platform as plat
                cloudflared_path = shutil.which('cloudflared')

                if cloudflared_path:
                    print(f"[SETTINGS] 🔄 Reiniciando túnel con ID: {tunnel_id}")

                    # Usar flags correctas según el sistema operativo
                    if plat.system() == 'Windows':
                        # Windows: usar creationflags para proceso detached y sin ventana
                        DETACHED_PROCESS = 0x00000008
                        CREATE_NO_WINDOW = 0x08000000
                        creation_flags = DETACHED_PROCESS | CREATE_NO_WINDOW

                        # Usar startupinfo para máxima ocultación
                        startupinfo = subprocess.STARTUPINFO()
                        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                        startupinfo.wShowWindow = 0  # SW_HIDE = 0

                        subprocess.Popen(
                            [cloudflared_path, 'tunnel', 'run', tunnel_id],
                            stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            creationflags=creation_flags,
                            startupinfo=startupinfo,
                            shell=False
                        )
                    else:
                        # Unix/Linux: usar start_new_session
                        subprocess.Popen(
                            [cloudflared_path, 'tunnel', 'run', tunnel_id],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            start_new_session=True
                        )

                    time.sleep(3)  # Esperar a que se inicie
                    print(f"[SETTINGS] ✅ Túnel reiniciado")

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
