#!/usr/bin/env python3
"""
================================================================================
Robot Runner - Windows Server Entry Point
================================================================================

Entry point para ejecutar el servidor Robot Runner en Windows usando Waitress.

Waitress es un servidor WSGI puro en Python, compatible con Windows.
No requiere fork() o señales Unix como Gunicorn.

Uso:
    python cli/run_server_windows.py
    python -m cli.run_server_windows

Características:
    - Servidor Waitress (compatible Windows)
    - Embedded Celery workers en threads
    - RabbitMQ broker + SQLite backend
    - SSL/TLS soporte
    - Cloudflare tunnel integration

Para más información, ver docs/TECHNICAL-DOCUMENTATION.md

================================================================================
"""
import os
import sys
import threading
from pathlib import Path

# Asegurar que el directorio raíz está en el path
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))


def main():
    """
    Punto de entrada del servidor para Windows.

    Ejecuta el servidor Flask con Waitress en modo producción.
    """
    # ========================================================================
    # VERIFICAR BROKER (RabbitMQ en Windows)
    # ========================================================================
    print("🔍 Verificando broker de Celery...")
    try:
        from shared.celery_app.config import BROKER_URL, BACKEND_TYPE
        import time

        print(f"   Tipo de backend: {BACKEND_TYPE}")

        # Detectar tipo de broker y verificar disponibilidad
        if 'amqp' in BROKER_URL:
            # RabbitMQ broker - verificar conexión TCP
            print("   Broker: RabbitMQ")
            try:
                import socket
                # Extract host and port from amqp URL
                if '://' in BROKER_URL:
                    parts = BROKER_URL.split('://')[1].split('@')
                    if len(parts) > 1:
                        host_port = parts[1].split('/')[0]
                        if ':' in host_port:
                            host, port = host_port.split(':')
                            port = int(port)
                        else:
                            host, port = host_port, 5672
                    else:
                        host, port = 'localhost', 5672
                else:
                    host, port = 'localhost', 5672

                # Test TCP connection to RabbitMQ
                max_attempts = 5
                for attempt in range(1, max_attempts + 1):
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(2)
                        result = sock.connect_ex((host, port))
                        sock.close()

                        if result == 0:
                            print(f"✅ RabbitMQ disponible en {host}:{port}")
                            break
                        else:
                            raise ConnectionError(f"No se pudo conectar a RabbitMQ en {host}:{port}")
                    except Exception as e:
                        if attempt == max_attempts:
                            print(f"❌ RabbitMQ no disponible después de {max_attempts} intentos: {e}")
                            print("   Asegúrate de tener RabbitMQ corriendo:")
                            print("   - Windows: net start RabbitMQ")
                            print("   - O desde Services: Iniciar servicio 'RabbitMQ'")
                            print("   - Management UI: http://localhost:15672")
                            sys.exit(1)
                        print(f"   ⏳ RabbitMQ no responde (intento {attempt}/{max_attempts}), reintentando...")
                        time.sleep(1)
            except Exception as e:
                print(f"❌ Error verificando RabbitMQ: {e}")
                sys.exit(1)

        elif 'redis' in BROKER_URL:
            # Redis broker (fallback)
            print("   Broker: Redis")
            try:
                from shared.state.redis_manager import redis_manager
                redis_manager.ensure_redis_running()
                print("✅ Redis está listo")
            except Exception as e:
                print(f"❌ Error con Redis: {e}")
                print("   Nota: En Windows se recomienda usar RabbitMQ")
                sys.exit(1)
        else:
            print(f"⚠️  Broker desconocido: {BROKER_URL}")
            print("   Continuando de todas formas...")

    except Exception as e:
        print(f"❌ Error verificando broker: {e}")
        sys.exit(1)

    # ========================================================================
    # VERIFICAR CONFIGURACIÓN
    # ========================================================================
    print("🔍 Verificando configuración...")
    try:
        from shared.config.loader import get_config_data
        config = get_config_data()

        # Validar campos críticos
        required_fields = ['port', 'machine_id', 'token']
        missing_fields = [field for field in required_fields if not config.get(field)]

        if missing_fields:
            print(f"⚠️  Faltan campos en config.json: {', '.join(missing_fields)}")
            print(f"   Editar: {Path.home() / 'Robot' / 'config.json'}")
            print("   O usar el endpoint /connect para configurar")

        port = config.get('port', 5055)
        machine_id = config.get('machine_id', 'N/A')
        print(f"✅ Configuración cargada (machine_id: {machine_id}, port: {port})")

    except Exception as e:
        print(f"❌ Error cargando configuración: {e}")
        sys.exit(1)

    # ========================================================================
    # INICIAR CELERY WORKERS EN THREADS
    # ========================================================================
    print("🔄 Iniciando Celery workers...")
    try:
        from shared.celery_app.worker import start_celery_worker_thread

        # Iniciar worker en thread
        worker_thread = start_celery_worker_thread()
        print(f"✅ Celery worker iniciado en thread: {worker_thread.name}")

    except Exception as e:
        print(f"⚠️  Error iniciando Celery worker: {e}")
        print("   El servidor continuará sin workers embebidos")

    # ========================================================================
    # EJECUTAR WAITRESS
    # ========================================================================

    try:
        from waitress import serve
        from api.app import create_app
        import socket

        # Crear aplicación Flask
        flask_app = create_app()

        # Detectar SSL antes de mostrar URLs
        ssl_folder = Path.home() / 'Robot' / 'ssl'
        cert_file = ssl_folder / 'cert.pem'
        key_file = ssl_folder / 'key.pem'
        ssl_enabled = cert_file.exists() and key_file.exists()
        protocol = 'https' if ssl_enabled else 'http'

        # Obtener IP local
        local_ip = '127.0.0.1'
        try:
            # Truco para obtener la IP local sin realmente conectarse
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except:
            local_ip = '127.0.0.1'

        # Obtener hostname del túnel si está configurado
        tunnel_hostname = config.get('tunnel_subdomain', '')
        if tunnel_hostname:
            # Normalizar hostname del túnel (usar función de utils)
            from shared.utils.tunnel import get_tunnel_hostname
            tunnel_hostname = get_tunnel_hostname(config)

        # Mostrar información de inicio
        print("\n" + "="*70)
        print("🚀 Iniciando Robot Runner Server (Windows)...")
        print("="*70)
        print(f"📍 Port: {port}")
        print(f"🔑 Machine ID: {machine_id}")
        print(f"🖥️  Servidor: Waitress (compatible Windows)")

        if ssl_enabled:
            print(f"🔒 SSL: Habilitado")
            print(f"   Certificado: {cert_file}")
            print(f"   Clave: {key_file}")
        else:
            print(f"🔓 SSL: No configurado")

        print("\n🌐 URLs de acceso:")
        print(f"   • Local:    {protocol}://localhost:{port}")
        print(f"   • Red:      {protocol}://{local_ip}:{port}")

        # Mostrar URL del túnel si está configurado
        if tunnel_hostname and tunnel_hostname != 'N/A':
            print(f"   • Túnel:    https://{tunnel_hostname}")
            print(f"     (requiere túnel activo - usar /tunnel/start)")

        print("="*70 + "\n")

        # IMPORTANTE: En Windows, usar 0.0.0.0 es correcto
        # Esto permite acceso desde:
        # - localhost (127.0.0.1) - necesario para el túnel Cloudflare
        # - IP local (ej: 192.168.x.x) - necesario para acceso de red local
        # - 0.0.0.0 escucha en todas las interfaces IPv4
        bind_host = '0.0.0.0'

        print(f"[SERVIDOR] Binding a: {bind_host}:{port} (todas las interfaces IPv4)")
        print(f"[SERVIDOR] El servidor responderá en:")
        print(f"           - localhost:{port} (para túnel Cloudflare)")
        print(f"           - {local_ip}:{port} (para red local)")
        print()

        # Configurar y ejecutar Waitress
        if ssl_enabled:
            # Waitress con SSL
            serve(
                flask_app,
                host=bind_host,
                port=port,
                threads=4,
                channel_timeout=300,
                url_scheme='https',
                ident='RobotRunner-Waitress/1.0'
            )
        else:
            # Waitress sin SSL
            serve(
                flask_app,
                host=bind_host,
                port=port,
                threads=4,
                channel_timeout=300,
                ident='RobotRunner-Waitress/1.0'
            )

    except KeyboardInterrupt:
        print("\n\n⚠️  Servidor interrumpido por el usuario (Ctrl+C)")
        print("🔄 Limpiando recursos...")

        # Detener workers
        try:
            from shared.celery_app.worker import stop_celery_worker_thread
            stop_celery_worker_thread()
            print("✅ Celery workers detenidos")
        except:
            pass

        sys.exit(0)

    except Exception as e:
        print(f"\n❌ Error al ejecutar el servidor: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()