#!/usr/bin/env python3
"""
================================================================================
Robot Runner - Server Entry Point
================================================================================

Entry point para ejecutar solo el servidor Robot Runner sin GUI.

Uso:
    python cli/run_server.py
    python -m cli.run_server

Características:
    - Inicia el servidor Flask con Gunicorn
    - Embedded Celery workers
    - Redis state management
    - SSL/TLS soporte
    - Cloudflare tunnel integration

Para más información, ver docs/TECHNICAL-DOCUMENTATION.md

================================================================================
"""
import os
import sys
from pathlib import Path

# Asegurar que el directorio raíz está en el path
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))


def main():
    """
    Punto de entrada del servidor.

    Ejecuta el servidor Flask con Gunicorn en modo producción.
    """
    # ========================================================================
    # FIX PARA macOS: Deshabilitar fork safety check de Objective-C
    # ========================================================================
    os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'

    # ========================================================================
    # VERIFICAR BROKER (Redis o RabbitMQ)
    # ========================================================================
    print("🔍 Verificando broker de Celery...")
    try:
        from shared.celery_app.config import BROKER_URL, BACKEND_TYPE
        import time

        print(f"   Tipo de backend: {BACKEND_TYPE}")

        # Detectar tipo de broker y verificar disponibilidad
        if 'redis' in BROKER_URL:
            # Redis broker - verificar con redis_manager
            print("   Broker: Redis")
            try:
                from shared.state.redis_manager import redis_manager
                redis_manager.ensure_redis_running()
                print("✅ Redis está listo")
            except Exception as e:
                print(f"❌ Error con Redis: {e}")
                print("   Asegúrate de tener Redis instalado:")
                print("   - macOS: brew install redis && brew services start redis")
                print("   - Linux: sudo apt-get install redis-server")
                sys.exit(1)

        elif 'amqp' in BROKER_URL:
            # RabbitMQ broker - verificar conexión TCP
            print("   Broker: RabbitMQ")
            try:
                import socket
                # Extract host and port from amqp URL
                # amqp://guest:guest@localhost:5672//
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
                            print("   - macOS: brew install rabbitmq && brew services start rabbitmq")
                            print("   - Linux: sudo apt-get install rabbitmq-server")
                            print("   - Windows: Descargar de https://www.rabbitmq.com/download.html")
                            sys.exit(1)
                        print(f"   ⏳ RabbitMQ no responde (intento {attempt}/{max_attempts}), reintentando...")
                        time.sleep(1)
            except Exception as e:
                print(f"❌ Error verificando RabbitMQ: {e}")
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
    # EJECUTAR GUNICORN
    # ========================================================================
    print("\n" + "="*70)
    print("🚀 Iniciando Robot Runner Server...")
    print("="*70)
    print(f"📍 Port: {port}")
    print(f"🔑 Machine ID: {machine_id}")
    print(f"🌐 URL: https://0.0.0.0:{port}")
    print("="*70 + "\n")

    try:
        import gunicorn.app.base

        class StandaloneApplication(gunicorn.app.base.BaseApplication):
            """Aplicación Gunicorn standalone."""

            def __init__(self, app, options=None):
                self.options = options or {}
                self.application = app
                super().__init__()

            def load_config(self):
                # Aplicar configuración desde gunicorn_config.py
                config_module = 'gunicorn_config'
                try:
                    __import__(config_module)
                    mod = sys.modules[config_module]

                    # Configuraciones válidas de Gunicorn (excluir imports y módulos)
                    import types
                    valid_config_keys = {
                        'bind', 'workers', 'threads', 'worker_class', 'timeout',
                        'graceful_timeout', 'keepalive', 'loglevel', 'accesslog',
                        'errorlog', 'preload_app', 'certfile', 'keyfile', 'proc_name'
                    }

                    # Copiar solo configuraciones válidas del módulo
                    for key, value in vars(mod).items():
                        if key.islower() and not key.startswith('_'):
                            # Filtrar módulos, funciones y tipos no serializables
                            if not isinstance(value, (types.ModuleType, types.FunctionType)):
                                if key in valid_config_keys:
                                    try:
                                        self.cfg.set(key, value)
                                    except Exception:
                                        pass  # Ignorar errores de configuración inválida

                    # Ejecutar hooks si existen
                    if hasattr(mod, 'post_worker_init'):
                        self.cfg.set('post_worker_init', mod.post_worker_init)
                    if hasattr(mod, 'worker_exit'):
                        self.cfg.set('worker_exit', mod.worker_exit)
                    if hasattr(mod, 'on_exit'):
                        self.cfg.set('on_exit', mod.on_exit)
                    if hasattr(mod, 'on_starting'):
                        self.cfg.set('on_starting', mod.on_starting)
                    if hasattr(mod, 'when_ready'):
                        self.cfg.set('when_ready', mod.when_ready)

                except ImportError as e:
                    print(f"⚠️  No se pudo cargar gunicorn_config.py: {e}")

                # Sobrescribir con options si las hay
                for key, value in self.options.items():
                    self.cfg.set(key.lower(), value)

            def load(self):
                return self.application

        # Crear aplicación Flask
        from api.app import create_app
        flask_app = create_app()

        # Opciones de Gunicorn (se sobrescriben con gunicorn_config.py)
        options = {
            'bind': f'0.0.0.0:{port}',
            'workers': 1,
            'threads': 4,
            'worker_class': 'sync',
            'timeout': 300,
        }

        # Ejecutar Gunicorn
        StandaloneApplication(flask_app, options).run()

    except KeyboardInterrupt:
        print("\n\n⚠️  Servidor interrumpido por el usuario (Ctrl+C)")
        print("🔄 Limpiando recursos...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error al ejecutar el servidor: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
