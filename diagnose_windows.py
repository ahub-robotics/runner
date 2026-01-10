#!/usr/bin/env python3
"""
Script de diagnóstico para Windows - Robot Runner

Verifica configuración y arranca el servidor con logs detallados.
"""
import sys
import os
from pathlib import Path

# Asegurar que el directorio raíz está en el path
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

def main():
    print("="*70)
    print("  🔍 DIAGNÓSTICO ROBOT RUNNER - WINDOWS")
    print("="*70)
    print()

    # 1. Verificar plataforma
    import platform
    print(f"1. Sistema operativo: {platform.system()} {platform.version()}")
    print(f"   Python: {sys.version}")
    print()

    # 2. Verificar broker
    print("2. Verificando broker RabbitMQ...")
    try:
        from shared.celery_app.config import BROKER_URL, BACKEND_TYPE
        print(f"   ✅ Broker URL: {BROKER_URL}")
        print(f"   ✅ Backend Type: {BACKEND_TYPE}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        sys.exit(1)
    print()

    # 3. Verificar configuración
    print("3. Verificando configuración...")
    try:
        from shared.config.loader import get_config_data
        config = get_config_data()
        port = config.get('port', 5055)
        machine_id = config.get('machine_id', 'N/A')
        print(f"   ✅ Port: {port}")
        print(f"   ✅ Machine ID: {machine_id}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        sys.exit(1)
    print()

    # 4. Verificar state backend
    print("4. Verificando state backend...")
    try:
        from shared.state.state import get_state_manager
        state_manager = get_state_manager()
        if state_manager.ping():
            print(f"   ✅ State backend: {type(state_manager.backend).__name__}")
        else:
            print(f"   ❌ State backend no responde")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        sys.exit(1)
    print()

    # 5. Test de Flask app
    print("5. Creando Flask app...")
    try:
        from api.app import create_app
        app = create_app()
        print(f"   ✅ Flask app creada")
        print(f"   ✅ Blueprints: {len(app.blueprints)}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    print()

    # 6. Iniciar Celery worker en background
    print("6. Iniciando Celery worker...")
    try:
        from shared.celery_app.worker import start_celery_worker_thread
        worker_thread = start_celery_worker_thread()
        print(f"   ✅ Worker thread: {worker_thread.name}")
        print(f"   ✅ Worker alive: {worker_thread.is_alive()}")

        # Esperar un poco para que arranque
        import time
        time.sleep(3)
        print(f"   ✅ Worker still alive: {worker_thread.is_alive()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        # Continuar sin worker
    print()

    # 7. Iniciar Waitress
    print("7. Iniciando servidor Waitress...")
    print(f"   URL: http://0.0.0.0:{port}")
    print()
    print("="*70)
    print("  ✅ ARRANCANDO SERVIDOR")
    print("="*70)
    print()

    try:
        from waitress import serve

        # Flush stdout/stderr antes de arrange
        sys.stdout.flush()
        sys.stderr.flush()

        # Serve es BLOQUEANTE
        serve(
            app,
            host='0.0.0.0',
            port=port,
            threads=4,
            channel_timeout=300,
            ident='RobotRunner-Waitress/1.0'
        )
    except KeyboardInterrupt:
        print("\n\n⚠️  Servidor detenido por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error ejecutando Waitress: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()