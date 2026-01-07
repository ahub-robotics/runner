import json
import os
import shutil
import sys
from pathlib import Path

user_dir = Path.home() / 'Robot'
user_dir.mkdir(exist_ok=True)
config_file = user_dir / 'config.json'


def get_resource_path(relative_path):
    """Obtén la ruta absoluta del archivo, ajustada para PyInstaller."""
    # Verifica si estamos en un paquete PyInstaller
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def write_to_config(config_data):
     # Crea el directorio si no existe
    try:
        #file = get_resource_path("config.json")
        with open(config_file, "w") as file:
            json.dump(config_data, file, indent=4)
    except Exception as e:
        print("Error al escribir en Config.json:", e)


def get_config_data():
    kwargs = {}
    if not os.path.isfile(config_file):
        shutil.copyfile(get_resource_path('config.json'), config_file)

    file = open(config_file, 'r')
    data = file.read()
    if data:
        json_data = json.loads(data)
        kwargs['url'] = json_data.get('url', "https://robot-console-a73e07ff7a0d.herokuapp.com/")
        kwargs['token'] = json_data.get('token', None)
        kwargs['machine_id'] = json_data.get('machine_id', None)
        kwargs['license_key'] = json_data.get('license_key', None)
        kwargs['folder'] = json_data.get('folder', f"{user_dir}/Robots")
        kwargs['ip'] = json_data.get('ip', os.popen('curl -s ifconfig.me').readline())
        kwargs['port'] = json_data.get('port', "8088")
        kwargs['tunnel_subdomain'] = json_data.get('tunnel_subdomain', '')
        kwargs['tunnel_id'] = json_data.get('tunnel_id', '3d7de42c-4a8a-4447-b14f-053cc485ce6b')

    return kwargs


# Alias para compatibilidad con otras partes del código
save_config_data = write_to_config


def get_args(parser, config):
    args = parser.parse_args()

    # Manejar comandos especiales primero
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

    # Actualizar configuración con argumentos CLI
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

    # Determinar si guardar la configuración
    # Por defecto: guardar si hay cambios en los argumentos
    # --save: forzar guardado
    # --no-save: no guardar
    config['_should_save'] = not args.no_save if args.save or has_cli_args(args) else False

    # Validar campos obligatorios solo si se proporcionan interactivamente
    for k in config:
        if k.startswith('_'):  # Ignorar campos internos como _should_save
            continue
        if config[k] is None:
            config[k] = input(f"Introduce {k}: ")

    return config


def has_cli_args(args):
    """Verifica si se proporcionó algún argumento de configuración."""
    config_args = ['url', 'token', 'machine_id', 'license_key', 'folder', 'ip', 'port', 'tunnel_subdomain', 'tunnel_id']
    return any(getattr(args, arg, None) is not None for arg in config_args)


def show_config(config):
    """Muestra la configuración actual en formato legible."""
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
    subdomain_base = config.get('tunnel_subdomain', '').strip()
    if not subdomain_base:
        subdomain_base = config.get('machine_id', '').strip()
    subdomain = f"{subdomain_base.lower()}.automatehub.es" if subdomain_base else 'N/A'
    print(f"  Subdominio:       {subdomain}")
    print(f"  Tunnel ID:        {config.get('tunnel_id', 'N/A')}")
    print("\n" + "=" * 60 + "\n")


def check_tunnel_status():
    """Verifica el estado del túnel de Cloudflare."""
    import subprocess
    print("\n" + "=" * 60)
    print("  Estado del Túnel de Cloudflare")
    print("=" * 60)

    try:
        result = subprocess.run(
            ['pgrep', '-f', 'cloudflared tunnel run'],
            capture_output=True,
            text=True
        )

        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            print(f"\n✅ Túnel ACTIVO")
            print(f"   PIDs: {', '.join(pids)}")

            # Obtener configuración para mostrar subdominio
            config = get_config_data()
            subdomain_base = config.get('tunnel_subdomain', '').strip()
            if not subdomain_base:
                subdomain_base = config.get('machine_id', '').strip()
            subdomain = f"{subdomain_base.lower()}.automatehub.es" if subdomain_base else 'N/A'
            print(f"   URL: https://{subdomain}")
        else:
            print(f"\n❌ Túnel INACTIVO")
            print(f"   Ejecuta: python run.py --start-tunnel")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

    print("\n" + "=" * 60 + "\n")


def start_tunnel_cli():
    """Inicia el túnel de Cloudflare desde CLI."""
    import subprocess
    import shutil
    import time
    from pathlib import Path

    print("\n" + "=" * 60)
    print("  Iniciando Túnel de Cloudflare")
    print("=" * 60 + "\n")

    try:
        # Verificar si cloudflared está instalado
        if not shutil.which('cloudflared'):
            print("❌ Error: cloudflared no está instalado")
            print("   Instalar con: brew install cloudflared")
            return

        # Verificar configuración
        cloudflare_config = Path.home() / '.cloudflared' / 'config.yml'
        if not cloudflare_config.exists():
            print("❌ Error: Configuración de túnel no encontrada")
            print("   Ejecutar primero: python run.py --setup-tunnel")
            return

        # Verificar si ya está corriendo
        result = subprocess.run(
            ['pgrep', '-f', 'cloudflared tunnel run'],
            capture_output=True,
            text=True
        )

        if result.stdout.strip():
            print("⚠️  El túnel ya está activo")
            return

        # Iniciar túnel
        print("🚀 Iniciando túnel...")
        subprocess.Popen(
            ['cloudflared', 'tunnel', 'run', 'robotrunner'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

        time.sleep(2)

        # Verificar que se inició
        result = subprocess.run(
            ['pgrep', '-f', 'cloudflared tunnel run'],
            capture_output=True,
            text=True
        )

        if result.stdout.strip():
            config = get_config_data()
            subdomain_base = config.get('tunnel_subdomain', '').strip()
            if not subdomain_base:
                subdomain_base = config.get('machine_id', '').strip()
            subdomain = f"{subdomain_base.lower()}.automatehub.es" if subdomain_base else 'N/A'

            print("✅ Túnel iniciado correctamente")
            print(f"   URL: https://{subdomain}")
        else:
            print("❌ Error al iniciar el túnel")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

    print("\n" + "=" * 60 + "\n")


def stop_tunnel_cli():
    """Detiene el túnel de Cloudflare desde CLI."""
    import subprocess

    print("\n" + "=" * 60)
    print("  Deteniendo Túnel de Cloudflare")
    print("=" * 60 + "\n")

    try:
        result = subprocess.run(
            ['pgrep', '-f', 'cloudflared tunnel run'],
            capture_output=True,
            text=True
        )

        if not result.stdout.strip():
            print("⚠️  No hay túneles activos")
            return

        pids = result.stdout.strip().split('\n')
        print(f"🛑 Deteniendo túnel (PIDs: {', '.join(pids)})...")

        for pid in pids:
            if pid:
                subprocess.run(['kill', pid], check=True)

        print("✅ Túnel detenido correctamente")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

    print("\n" + "=" * 60 + "\n")


def setup_tunnel_cli(config):
    """Configura el túnel de Cloudflare automáticamente."""
    import subprocess
    import shutil
    from pathlib import Path

    print("\n" + "=" * 60)
    print("  Configuración del Túnel de Cloudflare")
    print("=" * 60 + "\n")

    try:
        # Verificar si cloudflared está instalado
        if not shutil.which('cloudflared'):
            print("❌ Error: cloudflared no está instalado")
            print("   Instalar con: brew install cloudflared")
            return

        # Obtener machine_id y tunnel_id
        machine_id = config.get('machine_id', '').strip()
        if not machine_id:
            print("❌ Error: machine_id no configurado")
            print("   Ejecutar con: python run.py --machine_id=TU_ID --setup-tunnel")
            return

        tunnel_id = config.get('tunnel_id', '3d7de42c-4a8a-4447-b14f-053cc485ce6b')
        subdomain_base = config.get('tunnel_subdomain', machine_id)
        hostname = f"{subdomain_base.lower()}.automatehub.es"
        port = config.get('port', '5055')

        print(f"📋 Configurando túnel:")
        print(f"   Machine ID:  {machine_id}")
        print(f"   Subdominio:  {hostname}")
        print(f"   Puerto:      {port}")
        print(f"   Tunnel ID:   {tunnel_id}\n")

        # Crear directorio de configuración
        cloudflare_dir = Path.home() / '.cloudflared'
        cloudflare_dir.mkdir(parents=True, exist_ok=True)

        # Crear archivo de configuración
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

        # Crear ruta DNS
        print("🌐 Configurando DNS en Cloudflare...")
        result = subprocess.run(
            ['cloudflared', 'tunnel', 'route', 'dns', 'robotrunner', hostname],
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