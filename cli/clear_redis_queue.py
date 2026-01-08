#!/usr/bin/env python3
"""
================================================================================
Clear Redis Queue - Robot Runner
================================================================================

Utilidad para limpiar las colas de Redis y tareas antiguas de Celery.

Útil cuando:
- Hay tareas antiguas con paths obsoletos (ej: después de refactorización)
- Las colas tienen mensajes corruptos o inválidos
- Quieres reiniciar completamente el estado de Celery

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


def clear_redis_queues():
    """
    Limpia las colas de Redis y tareas antiguas de Celery.

    Acciones:
    - Purge de tareas pendientes en Celery
    - Elimina metadata de tareas antiguas
    - Limpia colas de mensajes
    - Elimina unacked messages
    """
    print("\n" + "="*70)
    print("  🧹 LIMPIEZA DE REDIS QUEUE - ROBOT RUNNER")
    print("="*70)
    print()

    try:
        import redis
        from shared.celery_app.config import celery_app

        # 1. Purge de Celery (tareas pendientes)
        print("📋 [1/4] Purgeando tareas pendientes de Celery...")
        try:
            purged = celery_app.control.purge()
            if purged:
                print(f"    ✅ {purged} tareas pendientes eliminadas")
            else:
                print(f"    ✓ No hay tareas pendientes")
        except Exception as e:
            print(f"    ⚠️  Celery purge falló: {e}")
            print(f"    (Esto es normal si el worker no está corriendo)")

        # 2. Conectar a Redis
        print("\n📋 [2/4] Conectando a Redis...")
        redis_client = redis.Redis(host='localhost', port=6378, db=0)
        redis_client.ping()
        print(f"    ✅ Conectado a Redis (puerto 6378)")

        # 3. Limpiar task metadata
        print("\n📋 [3/4] Limpiando task metadata...")
        task_keys = redis_client.keys('celery-task-meta-*')
        if task_keys:
            deleted = redis_client.delete(*task_keys)
            print(f"    ✅ {deleted} task metadata keys eliminados")
        else:
            print(f"    ✓ No hay task metadata para limpiar")

        # 4. Limpiar colas
        print("\n📋 [4/4] Limpiando colas de mensajes...")
        total_messages = 0
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

        # Resumen
        print("\n" + "="*70)
        print("  ✨ LIMPIEZA COMPLETADA")
        print("="*70)
        print()
        print("Resumen:")
        if purged:
            print(f"  • {purged} tareas pendientes eliminadas")
        if task_keys:
            print(f"  • {len(task_keys)} task metadata keys eliminados")
        if total_messages > 0:
            print(f"  • {total_messages} mensajes en cola eliminados")
        if unacked_keys:
            print(f"  • {len(unacked_keys)} unacked messages eliminados")

        if not any([purged, task_keys, total_messages, unacked_keys]):
            print(f"  • Redis ya estaba limpio, no había nada que eliminar")

        print()
        print("💡 Reinicia el servidor para aplicar cambios:")
        print("   python run.py")
        print()

        return True

    except redis.ConnectionError:
        print("\n❌ Error: No se pudo conectar a Redis")
        print("   Asegúrate de que Redis está corriendo en localhost:6378")
        print()
        print("   Iniciar Redis:")
        print("   - macOS: brew services start redis")
        print("   - Linux: sudo service redis-server start")
        print()
        return False

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
        success = clear_redis_queues()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Operación cancelada por el usuario")
        sys.exit(1)


if __name__ == '__main__':
    main()
