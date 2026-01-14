"""
CLI argument parsing and command handling module.

This module handles command-line interface arguments, special commands
(show-config, tunnel management), and configuration merging with CLI args.
"""
import subprocess
import shutil
import sys
import time
from pathlib import Path

from .loader import get_config_data, write_to_config
from shared.utils.process import is_cloudflared_running, find_cloudflared_processes, kill_process
from shared.utils.tunnel import get_tunnel_hostname


def get_args(parser, config):
    """
    Parse CLI arguments and merge with configuration.

    Handles special commands (show-config, tunnel management) that exit immediately.
    For regular arguments, merges CLI values into config dictionary.

    Determines if configuration should be saved based on:
        - --save flag forces save
        - --no-save flag prevents save
        - Default: save if CLI args were provided

    Prompts for required fields if they are None.

    Args:
        parser: argparse.ArgumentParser instance
        config: Dictionary with current configuration

    Returns:
        dict: Updated configuration with CLI args merged

    Side effects:
        - May call sys.exit(0) for special commands
        - Prompts stdin for missing required fields
        - Adds '_should_save' key to config
    """
    args = parser.parse_args()

    # Handle special commands first (these exit immediately)
    if args.show_config:
        show_config(config)
        sys.exit(0)

    if args.tunnel_status:
        check_tunnel_status()
        sys.exit(0)

    if args.start_tunnel:
        start_tunnel_cli()
        sys.exit(0)

    if args.stop_tunnel:
        stop_tunnel_cli()
        sys.exit(0)

    if args.setup_tunnel:
        setup_tunnel_cli(config)
        sys.exit(0)

    # Merge CLI arguments into configuration
    if args.url:
        config['url'] = args.url
    if args.token:
        config['token'] = args.token
    if args.machine_id:
        config['machine_id'] = args.machine_id
    if args.license_key:
        config['license_key'] = args.license_key
    if args.folder:
        config['folder'] = args.folder
    if args.ip:
        config['ip'] = args.ip
    if args.port:
        config['port'] = str(args.port)
    if args.tunnel_subdomain:
        config['tunnel_subdomain'] = args.tunnel_subdomain
    if args.tunnel_id:
        config['tunnel_id'] = args.tunnel_id

    # Determine if configuration should be saved
    # Default: save if there are CLI args, unless --no-save is specified
    # --save: force save even without args
    config['_should_save'] = not args.no_save if args.save or has_cli_args(args) else False

    # Prompt for missing required fields
    for k in config:
        if k.startswith('_'):  # Skip internal fields like _should_save
            continue
        if config[k] is None:
            config[k] = input(f"Introduce {k}: ")

    return config


def has_cli_args(args):
    """
    Check if any configuration argument was provided via CLI.

    Args:
        args: Parsed argparse arguments

    Returns:
        bool: True if any config argument was provided
    """
    config_args = ['url', 'token', 'machine_id', 'license_key', 'folder', 'ip', 'port', 'tunnel_subdomain', 'tunnel_id']
    return any(getattr(args, arg, None) is not None for arg in config_args)


def show_config(config):
    """
    Display current configuration in readable format.

    Shows formatted table with:
        - Server settings (URL, IP, port)
        - Authentication (token, machine_id, license_key - masked)
        - Robots directory
        - Cloudflare tunnel (subdomain, tunnel_id)

    Args:
        config: Configuration dictionary to display
    """
    print("\n" + "=" * 60)
    print("  Configuración Actual de Robot Runner")
    print("=" * 60)
    print(f"\n📡 Servidor:")
    print(f"  URL Orquestador:  {config.get('url', 'N/A')}")
    print(f"  IP:               {config.get('ip', 'N/A')}")
    print(f"  Puerto:           {config.get('port', 'N/A')}")
    print(f"\n🔑 Autenticación:")
    print(f"  Token:            {'*' * 20 if config.get('token') else 'N/A'}")
    print(f"  Machine ID:       {config.get('machine_id', 'N/A')}")
    print(f"  License Key:      {'*' * 30 if config.get('license_key') else 'N/A'}")
    print(f"\n📁 Robots:")
    print(f"  Directorio:       {config.get('folder', 'N/A')}")
    print(f"\n🌐 Túnel Cloudflare:")
    hostname = get_tunnel_hostname(config)
    print(f"  Subdominio:       {hostname}")
    print(f"  Tunnel ID:        {config.get('tunnel_id', 'N/A')}")
    print("\n" + "=" * 60 + "\n")


def check_tunnel_status():
    """
    Check if Cloudflare tunnel is currently running.

    Uses multiplataforma process utilities. Displays:
        - Active status with PIDs
        - Tunnel URL with configured subdomain
        - Instructions if inactive
    """
    print("\n" + "=" * 60)
    print("  Estado del Túnel de Cloudflare")
    print("=" * 60)

    try:
        # Verificar si está corriendo (multiplataforma)
        if is_cloudflared_running():
            pids = find_cloudflared_processes()
            print(f"\n✅ Túnel ACTIVO")
            print(f"   PIDs: {', '.join([str(pid) for pid in pids])}")

            # Get configuration to show hostname
            config = get_config_data()
            hostname = get_tunnel_hostname(config)
            print(f"   URL: https://{hostname}")
        else:
            print(f"\n❌ Túnel INACTIVO")
            print(f"   Ejecuta: python run.py --start-tunnel")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

    print("\n" + "=" * 60 + "\n")


def start_tunnel_cli():
    """
    Start Cloudflare tunnel from CLI.

    Checks:
        - cloudflared is installed
        - Configuration file exists at ~/.cloudflared/config.yml
        - Tunnel is not already running

    Starts tunnel as background process and verifies it started successfully.
    """
    print("\n" + "=" * 60)
    print("  Iniciando Túnel de Cloudflare")
    print("=" * 60 + "\n")

    try:
        # Check if cloudflared is installed
        if not shutil.which('cloudflared'):
            print("❌ Error: cloudflared no está instalado")
            print("   Instalar con: brew install cloudflared")
            return

        # Check configuration exists
        cloudflare_config = Path.home() / '.cloudflared' / 'config.yml'
        if not cloudflare_config.exists():
            print("❌ Error: Configuración de túnel no encontrada")
            print("   Ejecutar primero: python run.py --setup-tunnel")
            return

        # Get tunnel_id from config
        config = get_config_data()
        tunnel_id = config.get('tunnel_id')
        if not tunnel_id:
            print("❌ Error: tunnel_id no configurado en config.json")
            print("   Ejecutar primero: python run.py --setup-tunnel")
            return

        # Check if already running (multiplataforma)
        if is_cloudflared_running():
            print("⚠️  El túnel ya está activo")
            return

        # Start tunnel
        print(f"🚀 Iniciando túnel (ID: {tunnel_id})...")
        # En Windows, necesitamos el path completo del ejecutable
        cloudflared_path = shutil.which('cloudflared')
        subprocess.Popen(
            [cloudflared_path, 'tunnel', 'run', tunnel_id],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

        time.sleep(2)

        # Verify it started (multiplataforma)
        if is_cloudflared_running():
            hostname = get_tunnel_hostname(config)

            print("✅ Túnel iniciado correctamente")
            print(f"   URL: https://{hostname}")
        else:
            print("❌ Error al iniciar el túnel")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

    print("\n" + "=" * 60 + "\n")


def stop_tunnel_cli():
    """
    Stop Cloudflare tunnel from CLI.

    Finds all running cloudflared processes and kills them gracefully (multiplataforma).
    """
    print("\n" + "=" * 60)
    print("  Deteniendo Túnel de Cloudflare")
    print("=" * 60 + "\n")

    try:
        # Buscar procesos de cloudflared (multiplataforma)
        pids = find_cloudflared_processes()

        if not pids:
            print("⚠️  No hay túneles activos")
            return

        print(f"🛑 Deteniendo túnel (PIDs: {', '.join([str(pid) for pid in pids])})...")

        # Matar cada proceso (multiplataforma)
        for pid in pids:
            kill_process(pid)

        print("✅ Túnel detenido correctamente")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

    print("\n" + "=" * 60 + "\n")


def setup_tunnel_cli(config):
    """
    Configure Cloudflare tunnel automatically.

    Creates:
        - ~/.cloudflared/config.yml with tunnel configuration
        - DNS route in Cloudflare for subdomain

    Requires:
        - cloudflared installed
        - machine_id in config
        - tunnel_id in config

    Args:
        config: Configuration dictionary with machine_id and tunnel settings
    """
    print("\n" + "=" * 60)
    print("  Configuración del Túnel de Cloudflare")
    print("=" * 60 + "\n")

    try:
        # Check if cloudflared is installed
        if not shutil.which('cloudflared'):
            print("❌ Error: cloudflared no está instalado")
            print("   Instalar con: brew install cloudflared")
            return

        # Get machine_id and tunnel_id - handle None values
        machine_id = (config.get('machine_id') or '').strip()
        if not machine_id:
            print("❌ Error: machine_id no configurado")
            print("   Ejecutar con: python run.py --machine_id=TU_ID --setup-tunnel")
            return

        # Read tunnel_id from config - NO usar valor por defecto hardcoded
        tunnel_id = config.get('tunnel_id')
        if not tunnel_id:
            print("❌ Error: tunnel_id no configurado")
            print("   Ejecutar con: python run.py --tunnel_id=TU_TUNNEL_ID --setup-tunnel")
            return

        hostname = get_tunnel_hostname(config)
        port = config.get('port', '5055')

        print(f"📋 Configurando túnel:")
        print(f"   Machine ID:  {machine_id}")
        print(f"   Subdominio:  {hostname}")
        print(f"   Puerto:      {port}")
        print(f"   Tunnel ID:   {tunnel_id}\n")

        # Create configuration directory
        cloudflare_dir = Path.home() / '.cloudflared'
        cloudflare_dir.mkdir(parents=True, exist_ok=True)

        # Create configuration files
        config_path = cloudflare_dir / 'config.yml'
        credentials_path = cloudflare_dir / f'{tunnel_id}.json'

        config_content = f"""tunnel: {tunnel_id}
credentials-file: {credentials_path}

ingress:
  # Subdominio configurado: {hostname}
  - hostname: {hostname}
    service: https://localhost:{port}
    originRequest:
      noTLSVerify: true
  - service: http_status:404
"""

        with open(config_path, 'w') as f:
            f.write(config_content)

        print("✅ Archivo de configuración creado")

        # Create DNS route usando tunnel_id (NO 'robotrunner' hardcoded)
        print("🌐 Configurando DNS en Cloudflare...")
        result = subprocess.run(
            ['cloudflared', 'tunnel', 'route', 'dns', tunnel_id, hostname],
            capture_output=True,
            text=True
        )

        if result.returncode == 0 or 'already exists' in result.stderr.lower():
            print("✅ Ruta DNS configurada")
        else:
            print(f"⚠️  Advertencia DNS: {result.stderr}")

        print(f"\n✅ Configuración completa!")
        print(f"   Para iniciar el túnel: python run.py --start-tunnel")
        print(f"   URL del robot: https://{hostname}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")

    print("\n" + "=" * 60 + "\n")
