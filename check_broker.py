#!/usr/bin/env python3
"""
Script para verificar el estado del broker y backend de Celery.
"""
import sys
from pathlib import Path

# Añadir directorio raíz al path
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

def check_broker():
    """Verifica el estado del broker de Celery."""
    print("=" * 70)
    print("  🔍 VERIFICACIÓN DE BROKER - ROBOT RUNNER")
    print("=" * 70)
    print()

    try:
        # 1. Obtener configuración
        from shared.celery_app.config import BROKER_URL, BACKEND_TYPE
        import platform

        print("📋 CONFIGURACIÓN DETECTADA:")
        print(f"  Sistema operativo: {platform.system()}")
        print(f"  Broker URL: {BROKER_URL}")
        print(f"  Backend Type: {BACKEND_TYPE}")
        print()

        # 2. Verificar conectividad del broker
        print("📡 VERIFICANDO CONECTIVIDAD DEL BROKER...")

        if 'redis' in BROKER_URL:
            # ============================================================
            # REDIS BROKER
            # ============================================================
            print("  Tipo: Redis")

            import redis
            # Extraer host y port del URL
            if '://' in BROKER_URL:
                parts = BROKER_URL.split('://')[1].split(':')
                host = parts[0]
                port = int(parts[1].split('/')[0]) if len(parts) > 1 else 6379
            else:
                host, port = 'localhost', 6379

            try:
                client = redis.Redis(host=host, port=port, socket_connect_timeout=2)
                client.ping()
                print(f"  ✅ Redis conectado en {host}:{port}")

                # Info adicional
                info = client.info()
                print(f"  📊 Versión: {info.get('redis_version', 'N/A')}")
                print(f"  📊 Clientes conectados: {info.get('connected_clients', 'N/A')}")
                print(f"  📊 Memoria usada: {info.get('used_memory_human', 'N/A')}")
                return True
            except redis.ConnectionError as e:
                print(f"  ❌ Error conectando a Redis: {e}")
                print(f"  💡 Solución:")
                print(f"     macOS: brew services start redis")
                print(f"     Linux: sudo service redis-server start")
                return False

        elif 'amqp' in BROKER_URL:
            # ============================================================
            # RABBITMQ BROKER
            # ============================================================
            print("  Tipo: RabbitMQ")

            import socket
            # Extraer host y port del URL
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

            try:
                # Test TCP connection
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((host, port))
                sock.close()

                if result == 0:
                    print(f"  ✅ RabbitMQ conectado en {host}:{port}")
                    print(f"  💡 Management UI: http://{host}:15672")
                    print(f"     Usuario: guest / Contraseña: guest")
                    return True
                else:
                    raise ConnectionError(f"No se pudo conectar a {host}:{port}")
            except Exception as e:
                print(f"  ❌ Error conectando a RabbitMQ: {e}")
                print(f"  💡 Solución:")
                print(f"     macOS: brew services start rabbitmq")
                print(f"     Linux: sudo service rabbitmq-server start")
                print(f"     Windows: net start RabbitMQ")
                return False

        else:
            print(f"  ⚠️  Broker desconocido: {BROKER_URL}")
            return False

    except ImportError as e:
        print(f"\n❌ Error de import: {e}")
        print("  💡 Solución:")
        print("     pip install -r requirements.txt")
        return False

    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_celery():
    """Verifica el estado de Celery."""
    print()
    print("=" * 70)
    print("  🔍 VERIFICACIÓN DE CELERY")
    print("=" * 70)
    print()

    try:
        from shared.celery_app.config import celery_app

        print("📋 INSPECCIONANDO CELERY...")

        # Verificar workers activos
        try:
            inspect = celery_app.control.inspect()
            stats = inspect.stats()

            if stats:
                print(f"  ✅ Workers activos: {len(stats)}")
                for worker_name, worker_stats in stats.items():
                    print(f"     • {worker_name}")
            else:
                print(f"  ⚠️  No hay workers activos")
                print(f"  💡 Los workers se inician automáticamente con gunicorn")

            # Verificar tareas registradas
            registered = inspect.registered()
            if registered:
                print(f"\n  ✅ Tareas registradas:")
                for worker_name, tasks in registered.items():
                    print(f"     Worker: {worker_name}")
                    for task in tasks[:5]:  # Mostrar solo las primeras 5
                        print(f"       - {task}")
                    if len(tasks) > 5:
                        print(f"       ... y {len(tasks) - 5} más")

        except Exception as e:
            print(f"  ⚠️  No se pudo conectar a Celery: {e}")
            print(f"  💡 Esto es normal si el servidor no está corriendo")

        return True

    except Exception as e:
        print(f"❌ Error verificando Celery: {e}")
        return False


def check_state_backend():
    """Verifica el estado del backend de estado."""
    print()
    print("=" * 70)
    print("  🔍 VERIFICACIÓN DE STATE BACKEND")
    print("=" * 70)
    print()

    try:
        from shared.state.state import get_state_manager

        print("📋 VERIFICANDO STATE MANAGER...")

        try:
            state_manager = get_state_manager()

            # Test ping
            if state_manager.ping():
                print(f"  ✅ State backend conectado")
                print(f"  📊 Backend tipo: {type(state_manager.backend).__name__}")

                # Test básico de escritura/lectura
                test_key = 'test:health_check'
                state_manager.set(test_key, 'ok')
                value = state_manager.get(test_key)
                state_manager.delete(test_key)

                if value == 'ok':
                    print(f"  ✅ Test de escritura/lectura: OK")
                else:
                    print(f"  ⚠️  Test de escritura/lectura: FAIL")

                return True
            else:
                print(f"  ❌ State backend no responde al ping")
                return False

        except Exception as e:
            print(f"  ❌ Error conectando al state backend: {e}")
            return False

    except Exception as e:
        print(f"❌ Error verificando state backend: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Entry point del script."""
    broker_ok = check_broker()
    celery_ok = check_celery()
    state_ok = check_state_backend()

    print()
    print("=" * 70)
    print("  📊 RESUMEN")
    print("=" * 70)
    print()
    print(f"  Broker:        {'✅ OK' if broker_ok else '❌ FAIL'}")
    print(f"  Celery:        {'✅ OK' if celery_ok else '❌ FAIL'}")
    print(f"  State Backend: {'✅ OK' if state_ok else '❌ FAIL'}")
    print()

    if broker_ok and state_ok:
        print("  🎉 Sistema listo para funcionar!")
        print()
        print("  💡 Para iniciar el servidor:")
        print("     python run.py")
        print()
        return 0
    else:
        print("  ⚠️  Hay componentes que necesitan atención")
        print()
        return 1


if __name__ == '__main__':
    sys.exit(main())