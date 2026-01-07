#!/usr/bin/env python3
"""
Script de diagnóstico para el sistema de streaming.

Verifica:
- Conexión a Redis
- Registro de tareas de Celery
- Estado del streaming en Redis
"""
import sys
import os

# Agregar el directorio padre al path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_redis_connection():
    """Verifica que Redis esté funcionando."""
    print("=" * 60)
    print("TEST 1: Conexión a Redis")
    print("=" * 60)

    try:
        from src.redis_state import redis_state
        client = redis_state._get_redis_client()

        # Hacer un ping
        response = client.ping()
        print(f"✅ Redis PING: {response}")

        # Verificar estado de streaming
        state = client.hgetall('streaming:state')
        if state:
            print("\n📊 Estado de streaming en Redis:")
            for k, v in state.items():
                k_str = k.decode('utf-8') if isinstance(k, bytes) else k
                v_str = v.decode('utf-8') if isinstance(v, bytes) else v
                print(f"  - {k_str}: {v_str}")
        else:
            print("\n⚪ No hay estado de streaming en Redis (inactivo)")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_celery_tasks():
    """Verifica que las tareas de Celery estén registradas."""
    print("\n" + "=" * 60)
    print("TEST 2: Registro de tareas de Celery")
    print("=" * 60)

    try:
        from src.celery_config import celery_app

        # Listar todas las tareas registradas
        tasks = sorted(celery_app.tasks.keys())

        print(f"\n📋 Tareas registradas ({len(tasks)}):")
        for task in tasks:
            if not task.startswith('celery.'):
                print(f"  ✓ {task}")

        # Verificar tareas de streaming específicamente
        streaming_tasks = [
            'src.streaming_tasks.start_streaming_task',
            'src.streaming_tasks.stop_streaming_task',
            'src.streaming_tasks.get_streaming_status'
        ]

        print("\n🎬 Tareas de streaming:")
        all_registered = True
        for task in streaming_tasks:
            if task in tasks:
                print(f"  ✅ {task}")
            else:
                print(f"  ❌ {task} - NO REGISTRADA")
                all_registered = False

        return all_registered

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_celery_worker():
    """Verifica si hay workers de Celery activos."""
    print("\n" + "=" * 60)
    print("TEST 3: Workers de Celery")
    print("=" * 60)

    try:
        from src.celery_config import celery_app

        # Inspeccionar workers activos
        inspect = celery_app.control.inspect()

        # Obtener stats de workers
        stats = inspect.stats()

        if stats:
            print(f"\n✅ Workers activos: {len(stats)}")
            for worker_name, worker_stats in stats.items():
                print(f"\n  Worker: {worker_name}")
                print(f"    - Pool: {worker_stats.get('pool', {}).get('implementation', 'N/A')}")
                print(f"    - Concurrency: {worker_stats.get('pool', {}).get('max-concurrency', 'N/A')}")
        else:
            print("\n⚠️  No hay workers activos")
            print("   Ejecuta el servidor para iniciar los workers:")
            print("   $ python run.py")

        return stats is not None and len(stats) > 0

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_start_streaming():
    """Prueba iniciar el streaming (solo si no está activo)."""
    print("\n" + "=" * 60)
    print("TEST 4: Iniciar streaming (OPCIONAL)")
    print("=" * 60)

    try:
        from src.redis_state import redis_state
        from src.streaming_tasks import start_streaming_task

        client = redis_state._get_redis_client()

        # Verificar si ya está activo
        state = client.hgetall('streaming:state')
        if state and state.get(b'active') == b'true':
            print("⚠️  El streaming ya está activo. Saltando prueba.")
            return True

        # Preguntar al usuario
        response = input("\n¿Deseas iniciar el streaming como prueba? (s/n): ")
        if response.lower() != 's':
            print("❌ Prueba saltada por el usuario")
            return True

        print("\n🚀 Iniciando tarea de streaming...")
        task = start_streaming_task.delay(
            host='0.0.0.0',
            port=8765,
            fps=15,
            quality=75,
            use_ssl=True
        )

        print(f"✅ Tarea iniciada: {task.id}")
        print(f"   Estado: {task.state}")

        # Esperar un poco
        import time
        time.sleep(2)

        # Verificar estado en Redis
        state = client.hgetall('streaming:state')
        if state:
            print("\n📊 Estado en Redis después de iniciar:")
            for k, v in state.items():
                k_str = k.decode('utf-8') if isinstance(k, bytes) else k
                v_str = v.decode('utf-8') if isinstance(v, bytes) else v
                print(f"  - {k_str}: {v_str}")

            # Preguntar si detener
            response = input("\n¿Deseas detener el streaming ahora? (s/n): ")
            if response.lower() == 's':
                from src.streaming_tasks import stop_streaming_task
                stop_task = stop_streaming_task.delay()
                print(f"🛑 Tarea de detención enviada: {stop_task.id}")
                time.sleep(2)

                state = client.hgetall('streaming:state')
                if not state:
                    print("✅ Streaming detenido correctamente")
                else:
                    print("⚠️  El estado aún existe en Redis")
        else:
            print("❌ No se encontró estado en Redis después de iniciar")
            return False

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Ejecuta todos los tests."""
    print("\n" + "=" * 60)
    print("DIAGNÓSTICO DEL SISTEMA DE STREAMING")
    print("=" * 60)

    results = {
        'Redis': test_redis_connection(),
        'Tareas Celery': test_celery_tasks(),
        'Workers Celery': test_celery_worker(),
    }

    # Test opcional de streaming
    if all(results.values()):
        results['Streaming'] = test_start_streaming()

    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")

    all_passed = all(results.values())

    if all_passed:
        print("\n🎉 Todos los tests pasaron correctamente")
        return 0
    else:
        print("\n⚠️  Algunos tests fallaron. Revisa los logs arriba.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
