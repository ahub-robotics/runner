#!/usr/bin/env python3
"""
================================================================================
Clear Broker Queue - Robot Runner
================================================================================

Utilidad para limpiar las colas del broker (Redis o RabbitMQ) y tareas antiguas de Celery.

Útil cuando:
- Hay tareas antiguas con paths obsoletos (ej: después de refactorización)
- Las colas tienen mensajes corruptos o inválidos
- Quieres reiniciar completamente el estado de Celery

Soporta:
- Redis (Linux/macOS)
- RabbitMQ (Windows)

Uso:
    python cli/clear_redis_queue.py
    python -m cli.clear_redis_queue

================================================================================
"""
import sys
from pathlib import Path

# Asegurar que el directorio raíz está en el path
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))


def clear_broker_queues():
    """
    Limpia las colas del broker (Redis o RabbitMQ) y tareas antiguas de Celery.

    Auto-detecta el broker en uso y aplica la limpieza correspondiente.

    Acciones:
    - Purge de tareas pendientes en Celery
    - Elimina metadata de tareas antiguas (si aplica)
    - Limpia colas de mensajes del broker
    - Elimina unacked messages (si aplica)
    """
    try:
        from shared.celery_app.config import celery_app, BROKER_URL, BACKEND_TYPE

        print("\n" + "="*70)
        print("  🧹 LIMPIEZA DE BROKER QUEUE - ROBOT RUNNER")
        print("="*70)
        print()
        print(f"Broker detectado: {BROKER_URL}")
        print(f"Backend tipo: {BACKEND_TYPE}")
        print()

        # 1. Purge de Celery (funciona para ambos brokers)
        print("📋 [1/3] Purgeando tareas pendientes de Celery...")
        purged = 0
        try:
            purged = celery_app.control.purge()
            if purged:
                print(f"    ✅ {purged} tareas pendientes eliminadas")
            else:
                print(f"    ✓ No hay tareas pendientes")
        except Exception as e:
            print(f"    ⚠️  Celery purge falló: {e}")
            print(f"    (Esto es normal si el worker no está corriendo)")

        # 2. Detectar y limpiar según el broker
        if 'redis' in BROKER_URL:
            # ============================================================
            # REDIS BROKER
            # ============================================================
            print("\n📋 [2/3] Limpiando Redis broker...")
            task_keys = []
            total_messages = 0
            unacked_keys = []

            try:
                import redis

                # Extract host and port from redis URL
                if '://' in BROKER_URL:
                    parts = BROKER_URL.split('://')[1].split(':')
                    host = parts[0]
                    port = int(parts[1].split('/')[0]) if len(parts) > 1 else 6379
                else:
                    host, port = 'localhost', 6379

                redis_client = redis.Redis(host=host, port=port, db=0, socket_connect_timeout=5)
                redis_client.ping()
                print(f"    ✅ Conectado a Redis ({host}:{port})")

                # Limpiar task metadata
                task_keys = redis_client.keys('celery-task-meta-*')
                if task_keys:
                    deleted = redis_client.delete(*task_keys)
                    print(f"    ✅ {deleted} task metadata keys eliminados")
                else:
                    print(f"    ✓ No hay task metadata para limpiar")

                # Limpiar colas
                for queue_name in ['celery', 'default']:
                    length = redis_client.llen(queue_name)
                    if length > 0:
                        redis_client.delete(queue_name)
                        print(f"    ✅ Cola '{queue_name}' limpiada ({length} mensajes)")
                        total_messages += length
                    else:
                        print(f"    ✓ Cola '{queue_name}' ya estaba vacía")

                # Limpiar unacked messages
                unacked_keys = redis_client.keys('unacked*')
                if unacked_keys:
                    redis_client.delete(*unacked_keys)
                    print(f"    ✅ {len(unacked_keys)} unacked keys eliminados")

            except redis.ConnectionError:
                print(f"    ❌ No se pudo conectar a Redis en {host}:{port}")
                print("    Asegúrate de que Redis está corriendo:")
                print("    - macOS: brew services start redis")
                print("    - Linux: sudo service redis-server start")
                return False
            except Exception as e:
                print(f"    ❌ Error limpiando Redis: {e}")
                import traceback
                traceback.print_exc()
                return False

        elif 'amqp' in BROKER_URL:
            # ============================================================
            # RABBITMQ BROKER
            # ============================================================
            print("\n📋 [2/3] Limpiando RabbitMQ broker...")
            total_messages = 0

            try:
                import pika

                # Extract connection params from amqp URL
                # amqp://guest:guest@localhost:5672//
                if '://' in BROKER_URL:
                    parts = BROKER_URL.split('://')[1]
                    # Extract credentials
                    if '@' in parts:
                        creds_part, host_part = parts.split('@')
                        if ':' in creds_part:
                            username, password = creds_part.split(':')
                        else:
                            username, password = creds_part, 'guest'
                    else:
                        username, password = 'guest', 'guest'
                        host_part = parts

                    # Extract host and port
                    host_port = host_part.split('/')[0]
                    if ':' in host_port:
                        host, port = host_port.split(':')
                        port = int(port)
                    else:
                        host, port = host_port, 5672
                else:
                    host, port = 'localhost', 5672
                    username, password = 'guest', 'guest'

                # Conectar a RabbitMQ
                credentials = pika.PlainCredentials(username, password)
                parameters = pika.ConnectionParameters(
                    host=host,
                    port=port,
                    credentials=credentials,
                    connection_attempts=3,
                    retry_delay=1
                )

                connection = pika.BlockingConnection(parameters)
                channel = connection.channel()
                print(f"    ✅ Conectado a RabbitMQ ({host}:{port})")

                # Purge colas principales
                for queue_name in ['celery', 'default']:
                    try:
                        # Declarar cola (idempotente)
                        channel.queue_declare(queue=queue_name, durable=True)
                        # Purge
                        method = channel.queue_purge(queue=queue_name)
                        message_count = method.method.message_count
                        if message_count > 0:
                            print(f"    ✅ Cola '{queue_name}' limpiada ({message_count} mensajes)")
                            total_messages += message_count
                        else:
                            print(f"    ✓ Cola '{queue_name}' ya estaba vacía")
                    except Exception as e:
                        print(f"    ⚠️  No se pudo purgar cola '{queue_name}': {e}")

                connection.close()
                print(f"    ✅ RabbitMQ limpiado correctamente")

            except ImportError:
                print(f"    ❌ Error: pika no está instalado")
                print("    Instalar con: pip install pika")
                return False
            except pika.exceptions.AMQPConnectionError:
                print(f"    ❌ No se pudo conectar a RabbitMQ en {host}:{port}")
                print("    Asegúrate de que RabbitMQ está corriendo:")
                print("    - macOS: brew services start rabbitmq")
                print("    - Linux: sudo service rabbitmq-server start")
                print("    - Windows: Iniciar desde Services o RabbitMQ Command Prompt")
                return False
            except Exception as e:
                print(f"    ❌ Error limpiando RabbitMQ: {e}")
                import traceback
                traceback.print_exc()
                return False

        else:
            print(f"\n⚠️  Broker desconocido: {BROKER_URL}")
            print("   Solo se purgaron tareas de Celery")

        # 3. Limpiar state backend (siempre)
        print("\n📋 [3/3] Limpiando state backend...")
        try:
            from shared.state.state import get_state_manager
            state_manager = get_state_manager()

            # Limpiar estados de streaming huérfanos
            streaming_keys = ['streaming:state', 'streaming:stop_requested', 'streaming:last_client_activity']
            cleaned = 0
            for key in streaming_keys:
                try:
                    state_manager.delete(key)
                    cleaned += 1
                except:
                    pass

            if cleaned > 0:
                print(f"    ✅ {cleaned} claves de streaming limpiadas")
            else:
                print(f"    ✓ State backend ya estaba limpio")

        except Exception as e:
            print(f"    ⚠️  Error limpiando state backend: {e}")

        # Resumen
        print("\n" + "="*70)
        print("  ✨ LIMPIEZA COMPLETADA")
        print("="*70)
        print()
        print("Resumen:")
        if purged:
            print(f"  • {purged} tareas pendientes eliminadas (Celery)")

        if 'redis' in BROKER_URL:
            if task_keys:
                print(f"  • {len(task_keys)} task metadata keys eliminados (Redis)")
            if total_messages > 0:
                print(f"  • {total_messages} mensajes en cola eliminados (Redis)")
            if unacked_keys:
                print(f"  • {len(unacked_keys)} unacked messages eliminados (Redis)")
        elif 'amqp' in BROKER_URL:
            if total_messages > 0:
                print(f"  • {total_messages} mensajes en cola eliminados (RabbitMQ)")

        if 'redis' in BROKER_URL:
            if not any([purged, task_keys, total_messages, unacked_keys]):
                print(f"  • Broker ya estaba limpio, no había nada que eliminar")
        elif 'amqp' in BROKER_URL:
            if not any([purged, total_messages]):
                print(f"  • Broker ya estaba limpio, no había nada que eliminar")

        print()
        print("💡 Reinicia el servidor para aplicar cambios:")
        print("   python run.py")
        print()

        return True

    except ImportError as e:
        print(f"\n❌ Error de import: {e}")
        print("   Asegúrate de tener todas las dependencias instaladas:")
        print("   pip install -r requirements.txt")
        print()
        return False

    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Entry point del script."""
    try:
        success = clear_broker_queues()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Operación cancelada por el usuario")
        sys.exit(1)


if __name__ == '__main__':
    main()
