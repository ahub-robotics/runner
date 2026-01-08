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
    # VERIFICAR REDIS
    # ========================================================================
    print("🔍 Verificando Redis...")
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

                    # Copiar configuración del módulo
                    for key, value in vars(mod).items():
                        if key.islower() and not key.startswith('_'):
                            self.cfg.set(key, value)

                    # Ejecutar hooks si existen
                    if hasattr(mod, 'post_worker_init'):
                        self.cfg.set('post_worker_init', mod.post_worker_init)
                    if hasattr(mod, 'worker_exit'):
                        self.cfg.set('worker_exit', mod.worker_exit)
                    if hasattr(mod, 'on_exit'):
                        self.cfg.set('on_exit', mod.on_exit)

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
