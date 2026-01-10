#!/usr/bin/env python3
"""
Script de configuración de Cloudflare Tunnel multiplataforma.

Funciona en Windows, Linux y macOS.
Configura automáticamente el tunnel y lo instala como servicio/daemon.

Uso:
    python setup_tunnel.py

    # O como módulo
    python -m setup_tunnel
"""
import sys
import os
import json
import subprocess
import platform
from pathlib import Path


class Colors:
    """Códigos de color ANSI para la terminal."""
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    GRAY = '\033[90m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Imprime un encabezado."""
    print(f"\n{Colors.CYAN}{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}{Colors.RESET}\n")


def print_step(number, text):
    """Imprime un paso numerado."""
    print(f"{Colors.YELLOW}{number}. {text}{Colors.RESET}")


def print_success(text):
    """Imprime un mensaje de éxito."""
    print(f"{Colors.GREEN}   ✅ {text}{Colors.RESET}")


def print_error(text):
    """Imprime un mensaje de error."""
    print(f"{Colors.RED}   ❌ {text}{Colors.RESET}")


def print_warning(text):
    """Imprime una advertencia."""
    print(f"{Colors.YELLOW}   ⚠️  {text}{Colors.RESET}")


def print_info(text):
    """Imprime información."""
    print(f"{Colors.GRAY}   {text}{Colors.RESET}")


def run_command(cmd, check=True, capture=True):
    """
    Ejecuta un comando del sistema.

    Args:
        cmd: Lista con el comando y argumentos
        check: Si True, lanza excepción en error
        capture: Si True, captura stdout/stderr

    Returns:
        subprocess.CompletedProcess
    """
    try:
        if capture:
            return subprocess.run(
                cmd,
                check=check,
                capture_output=True,
                text=True
            )
        else:
            return subprocess.run(cmd, check=check)
    except subprocess.CalledProcessError as e:
        if check:
            raise
        return e


def check_cloudflared():
    """Verifica si cloudflared está instalado."""
    print_step(1, "Verificando cloudflared...")

    try:
        result = run_command(['cloudflared', '--version'])
        version = result.stdout.strip()
        print_success(f"cloudflared instalado: {version}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_error("cloudflared no está instalado")
        print_info("Instalar:")

        system = platform.system()
        if system == 'Windows':
            print_info("  choco install cloudflared")
            print_info("  O descargar: https://github.com/cloudflare/cloudflared/releases")
        elif system == 'Darwin':
            print_info("  brew install cloudflared")
        else:  # Linux
            print_info("  wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64")
            print_info("  sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared")
            print_info("  sudo chmod +x /usr/local/bin/cloudflared")

        return False


def get_cloudflared_dir():
    """Obtiene el directorio de configuración de cloudflared."""
    return Path.home() / '.cloudflared'


def find_tunnel_credentials():
    """Encuentra archivos de credenciales de tunnel."""
    print_step(2, "Detectando tunnels...")

    cloudflared_dir = get_cloudflared_dir()

    if not cloudflared_dir.exists():
        print_error(f"No se encontró directorio: {cloudflared_dir}")
        print_info("Ejecutar primero: cloudflared tunnel login")
        return None

    print_info(f"Directorio: {cloudflared_dir}")

    # Buscar archivos .json (credenciales de tunnel)
    cred_files = list(cloudflared_dir.glob('*.json'))

    if not cred_files:
        print_error("No se encontraron credenciales de tunnel")
        print_info("Crear un tunnel con: cloudflared tunnel create <nombre>")
        return None

    if len(cred_files) == 1:
        cred_file = cred_files[0]
    else:
        print_warning(f"Se encontraron {len(cred_files)} tunnels:")
        for i, f in enumerate(cred_files):
            print_info(f"  [{i}] {f.stem}")

        while True:
            try:
                selection = input(f"{Colors.CYAN}   Selecciona el número del tunnel [0]: {Colors.RESET}").strip()
                if not selection:
                    selection = 0
                else:
                    selection = int(selection)

                if 0 <= selection < len(cred_files):
                    cred_file = cred_files[selection]
                    break
                else:
                    print_error("Selección inválida")
            except ValueError:
                print_error("Ingresa un número válido")

    tunnel_id = cred_file.stem
    print_success(f"Tunnel ID: {tunnel_id}")
    print_success(f"Credenciales: {cred_file}")

    return {
        'id': tunnel_id,
        'credentials_file': str(cred_file)
    }


def get_tunnel_config():
    """Solicita configuración del tunnel al usuario."""
    print_step(3, "Configuración del tunnel...")
    print()

    # Hostname
    print(f"{Colors.CYAN}   Ingresa el hostname (subdominio) del tunnel:{Colors.RESET}")
    print_info("Ejemplo: robot.tudominio.com")
    while True:
        hostname = input(f"{Colors.CYAN}   Hostname: {Colors.RESET}").strip()
        if hostname:
            break
        print_error("Hostname es requerido")

    # Puerto
    print()
    print(f"{Colors.CYAN}   Ingresa el puerto de Robot Runner (default: 8088):{Colors.RESET}")
    port_input = input(f"{Colors.CYAN}   Puerto [8088]: {Colors.RESET}").strip()
    port = port_input if port_input else "8088"

    print()
    print_success(f"Hostname: {hostname}")
    print_success(f"Puerto: {port}")

    return {
        'hostname': hostname,
        'port': port
    }


def create_config_file(tunnel_info, config):
    """Crea el archivo de configuración config.yml."""
    print_step(4, "Creando archivo de configuración...")

    cloudflared_dir = get_cloudflared_dir()
    config_path = cloudflared_dir / 'config.yml'

    # Backup del config anterior
    if config_path.exists():
        import datetime
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = config_path.with_suffix(f'.yml.backup.{timestamp}')
        config_path.rename(backup_path)
        print_info(f"Backup creado: {backup_path}")

    # Crear contenido del config
    config_content = f"""tunnel: {tunnel_info['id']}
credentials-file: {tunnel_info['credentials_file']}

ingress:
  - hostname: {config['hostname']}
    service: http://localhost:{config['port']}
  - service: http_status:404
"""

    # Escribir archivo
    config_path.write_text(config_content, encoding='utf-8')
    print_success(f"Configuración creada: {config_path}")

    print()
    print(f"{Colors.GRAY}   ─────────────────────────────────────────{Colors.RESET}")
    print(f"{Colors.GRAY}{config_content}{Colors.RESET}", end='')
    print(f"{Colors.GRAY}   ─────────────────────────────────────────{Colors.RESET}")

    return config_path


def install_service():
    """Instala cloudflared como servicio según el SO."""
    print_step(5, "Instalación como servicio...")

    system = platform.system()

    # Preguntar al usuario
    print()
    response = input(f"{Colors.CYAN}   ¿Instalar como servicio? (s/n) [s]: {Colors.RESET}").strip().lower()

    if response and response not in ['s', 'y', 'yes', 'si', 'sí']:
        print_info("Instalación de servicio omitida")
        print_info("Para iniciar manualmente: cloudflared tunnel run")
        return False

    print()

    if system == 'Windows':
        return install_service_windows()
    elif system == 'Linux':
        return install_service_linux()
    elif system == 'Darwin':
        return install_service_macos()
    else:
        print_error(f"Sistema operativo no soportado: {system}")
        return False


def install_service_windows():
    """Instala cloudflared como servicio en Windows."""
    print_warning("Se requieren permisos de Administrador")
    print_info("Instalando servicio en Windows...")

    try:
        # Verificar si ya existe
        result = run_command(['sc', 'query', 'cloudflared'], check=False)
        if result.returncode == 0:
            print_warning("Servicio ya existe, reinstalando...")
            run_command(['cloudflared', 'service', 'uninstall'], check=False)
            import time
            time.sleep(2)

        # Instalar
        run_command(['cloudflared', 'service', 'install'])
        print_success("Servicio instalado correctamente")

        # Iniciar
        print_info("Iniciando servicio...")
        run_command(['sc', 'start', 'cloudflared'])

        import time
        time.sleep(3)

        # Verificar estado
        result = run_command(['sc', 'query', 'cloudflared'])
        if 'RUNNING' in result.stdout:
            print_success("Servicio iniciado correctamente")
            return True
        else:
            print_warning("Servicio instalado pero no está corriendo")
            print_info("Iniciar con: sc start cloudflared")
            return False

    except subprocess.CalledProcessError as e:
        print_error(f"Error al instalar servicio: {e}")
        print_info("Ejecuta este script como Administrador")
        print_info("O instala manualmente: cloudflared service install")
        return False


def install_service_linux():
    """Instala cloudflared como servicio systemd en Linux."""
    print_info("Instalando servicio systemd en Linux...")

    try:
        # Instalar servicio
        run_command(['sudo', 'cloudflared', 'service', 'install'])
        print_success("Servicio instalado correctamente")

        # Habilitar e iniciar
        print_info("Iniciando servicio...")
        run_command(['sudo', 'systemctl', 'enable', 'cloudflared'])
        run_command(['sudo', 'systemctl', 'start', 'cloudflared'])

        import time
        time.sleep(2)

        # Verificar estado
        result = run_command(['sudo', 'systemctl', 'is-active', 'cloudflared'], check=False)
        if result.stdout.strip() == 'active':
            print_success("Servicio iniciado correctamente")
            return True
        else:
            print_warning("Servicio instalado pero no está activo")
            print_info("Verificar con: sudo systemctl status cloudflared")
            return False

    except subprocess.CalledProcessError as e:
        print_error(f"Error al instalar servicio: {e}")
        print_info("Ejecuta con sudo o instala manualmente")
        return False


def install_service_macos():
    """Instala cloudflared como servicio en macOS."""
    print_info("Instalando servicio en macOS...")

    try:
        # Instalar servicio
        run_command(['sudo', 'cloudflared', 'service', 'install'])
        print_success("Servicio instalado correctamente")

        # Iniciar
        print_info("Iniciando servicio...")
        run_command(['sudo', 'launchctl', 'start', 'com.cloudflare.cloudflared'])

        import time
        time.sleep(2)

        print_success("Servicio iniciado")
        print_info("Verificar con: sudo launchctl list | grep cloudflared")
        return True

    except subprocess.CalledProcessError as e:
        print_error(f"Error al instalar servicio: {e}")
        print_info("Ejecuta con sudo o instala manualmente")
        return False


def print_summary(tunnel_info, config, config_path, service_installed):
    """Imprime resumen de la configuración."""
    print_header("✅ CONFIGURACIÓN COMPLETADA")

    print(f"{Colors.CYAN}📋 Resumen:{Colors.RESET}")
    print(f"{Colors.BOLD}   • Tunnel ID:{Colors.RESET} {tunnel_info['id']}")
    print(f"{Colors.BOLD}   • Hostname:{Colors.RESET} {config['hostname']}")
    print(f"{Colors.BOLD}   • Puerto local:{Colors.RESET} {config['port']}")
    print(f"{Colors.BOLD}   • Config:{Colors.RESET} {config_path}")
    print()

    print(f"{Colors.CYAN}🌐 Acceso:{Colors.RESET}")
    print(f"{Colors.BOLD}   https://{config['hostname']}{Colors.RESET}")
    print()

    if service_installed:
        print(f"{Colors.CYAN}🔧 Comandos útiles:{Colors.RESET}")

        system = platform.system()
        if system == 'Windows':
            print_info("Ver estado: sc query cloudflared")
            print_info("Iniciar: sc start cloudflared")
            print_info("Detener: sc stop cloudflared")
            print_info("Logs: Get-EventLog -LogName Application -Source cloudflared -Newest 20")
        elif system == 'Linux':
            print_info("Ver estado: sudo systemctl status cloudflared")
            print_info("Iniciar: sudo systemctl start cloudflared")
            print_info("Detener: sudo systemctl stop cloudflared")
            print_info("Logs: sudo journalctl -u cloudflared -n 50")
        elif system == 'Darwin':
            print_info("Ver estado: sudo launchctl list | grep cloudflared")
            print_info("Detener: sudo launchctl stop com.cloudflare.cloudflared")
            print_info("Logs: sudo tail -f /var/log/cloudflared.log")
        print()

    print(f"{Colors.GREEN}✨ El tunnel está configurado y listo!{Colors.RESET}\n")


def main():
    """Función principal."""
    print_header("🌐 CONFIGURACIÓN CLOUDFLARE TUNNEL")

    print(f"{Colors.CYAN}Sistema operativo:{Colors.RESET} {platform.system()} {platform.release()}")
    print()

    # 1. Verificar cloudflared
    if not check_cloudflared():
        sys.exit(1)
    print()

    # 2. Detectar tunnel
    tunnel_info = find_tunnel_credentials()
    if not tunnel_info:
        sys.exit(1)
    print()

    # 3. Obtener configuración
    config = get_tunnel_config()
    print()

    # 4. Crear archivo de configuración
    config_path = create_config_file(tunnel_info, config)
    print()

    # 5. Instalar como servicio
    service_installed = install_service()
    print()

    # 6. Resumen
    print_summary(tunnel_info, config, config_path, service_installed)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⚠️  Configuración cancelada por el usuario{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}❌ Error inesperado: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)