"""
Celery Tasks for Robot Runner

Este módulo define las tareas de Celery para ejecutar robots de manera asíncrona.

Tareas:
    - run_robot_task: Tarea principal que ejecuta un robot
    - cleanup_old_executions: Tarea periódica para limpiar ejecuciones antiguas
"""
import time

from shared.celery_app.config import celery_app
from shared.config.loader import get_config_data
from .server import Server


@celery_app.task(bind=True, name='executors.tasks.run_robot_task')
def run_robot_task(self, data):
    """
    Tarea de Celery que ejecuta un robot.

    Args:
        self: Task instance (bind=True)
        data: Diccionario con datos de ejecución (robot, execution, branch, params)

    Returns:
        dict: Resultado de la ejecución con exit_code y status
    """
    execution_id = data.get('execution_id')
    task_id = self.request.id

    print(f"[TASK] Iniciando tarea Celery")
    print(f"[TASK] - Task ID: {task_id}")
    print(f"[TASK] - Execution ID: {execution_id}")

    try:
        # Importar redis_state aquí para evitar importación circular
        from shared.state.redis_state import redis_state

        # IMPORTANTE: NO sobrescribir el estado aquí - ya está establecido desde /run
        # Solo actualizar que la tarea Celery inició (agregar started_at si no existe)
        existing_state = redis_state.load_execution_state(execution_id)
        if existing_state and not existing_state.get('started_at'):
            redis_state.save_execution_state(execution_id, {
                'started_at': time.time()
            })

        print(f"[TASK] Creando instancia de Server")
        # Crear instancia de Server con configuración
        config = get_config_data()
        server = Server(config)

        # Configurar execution_id en el server
        server.execution_id = execution_id

        print(f"[TASK] Ejecutando robot (bloqueante)")
        # Ejecutar robot (bloqueante) - esto llama a server.run(data)
        server.run(data)

        print(f"[TASK] Robot ejecutado, obteniendo exit code")
        # Obtener exit code guardado por server.run()
        exit_code = getattr(server, 'last_exit_code', None)

        if exit_code is None:
            print(f"[TASK] ⚠️  No se pudo obtener exit code, asumiendo error")
            exit_code = 1  # Error por defecto

        print(f"[TASK] Exit code: {exit_code}")

        # Determinar estado final
        if exit_code == 0:
            final_status = 'completed'
        elif exit_code == 15:
            final_status = 'completed'  # Detenido grácilmente
        else:
            final_status = 'failed'

        # Actualizar estado final en Redis
        redis_state.save_execution_state(execution_id, {
            'status': final_status,
            'exit_code': exit_code,
            'finished_at': time.time()
        })

        print(f"[TASK] ✅ Tarea completada: {final_status} (exit_code={exit_code})")

        return {
            'execution_id': execution_id,
            'task_id': task_id,
            'exit_code': exit_code,
            'status': final_status
        }

    except Exception as e:
        print(f"[TASK] ❌ Error en tarea: {e}")
        import traceback
        traceback.print_exc()

        # Actualizar estado de error en Redis
        try:
            from shared.state.redis_state import redis_state
            redis_state.save_execution_state(execution_id, {
                'status': 'failed',
                'exit_code': 1,
                'error': str(e),
                'finished_at': time.time()
            })
        except Exception as redis_error:
            print(f"[TASK] ⚠️  No se pudo actualizar estado de error en Redis: {redis_error}")

        # Re-raise la excepción para que Celery la marque como fallida
        raise


@celery_app.task(name='executors.tasks.cleanup_old_executions')
def cleanup_old_executions(max_age_hours=24):
    """
    Tarea periódica para limpiar ejecuciones antiguas de Redis.

    Args:
        max_age_hours: Edad máxima en horas (por defecto 24h)

    Returns:
        dict: Número de ejecuciones eliminadas
    """
    try:
        from shared.state.redis_state import redis_state
        import time

        print(f"[CLEANUP] Iniciando limpieza de ejecuciones > {max_age_hours}h")

        # Obtener todas las claves de ejecuciones
        redis_client = redis_state._get_redis_client()
        execution_keys = redis_client.keys('execution:*')

        # Filtrar solo las claves principales (no :pause_control)
        execution_keys = [k.decode('utf-8') if isinstance(k, bytes) else k
                         for k in execution_keys
                         if ':pause_control' not in (k.decode('utf-8') if isinstance(k, bytes) else k)]

        deleted_count = 0
        now = time.time()
        max_age_seconds = max_age_hours * 3600

        for key in execution_keys:
            # Obtener información de la ejecución
            exec_data = redis_client.hgetall(key)

            if not exec_data:
                continue

            # Decodificar datos
            exec_data = {k.decode('utf-8'): v.decode('utf-8')
                        for k, v in exec_data.items()}

            # Verificar edad
            finished_at = exec_data.get('finished_at')
            if finished_at:
                try:
                    age = now - float(finished_at)
                    if age > max_age_seconds:
                        # Eliminar clave de ejecución y control de pausa
                        execution_id = key.replace('execution:', '')
                        redis_client.delete(key)
                        redis_client.delete(f'execution:{execution_id}:pause_control')
                        deleted_count += 1
                        print(f"[CLEANUP] Eliminada ejecución antigua: {execution_id} (edad: {age/3600:.1f}h)")
                except (ValueError, TypeError):
                    print(f"[CLEANUP] ⚠️  Error al parsear finished_at para {key}")

        print(f"[CLEANUP] ✅ Limpieza completada: {deleted_count} ejecuciones eliminadas")

        return {
            'deleted_count': deleted_count,
            'checked_count': len(execution_keys)
        }

    except Exception as e:
        print(f"[CLEANUP] ❌ Error en limpieza: {e}")
        import traceback
        traceback.print_exc()
        raise
