"""
Redis State Manager for Robot Runner

Este módulo gestiona el estado compartido de ejecuciones usando Redis como backend.
Reemplaza el archivo JSON ~/Robot/robotrunner_state.json con una solución más robusta.

Estructura de claves en Redis:
    - execution:{id} (Hash): Estado de la ejecución
    - execution:{id}:pause_control (Hash): Control de pause/resume
    - server:{machine_id}:status (String): Estado del servidor
"""
import redis
import time
import os
from typing import Dict, Optional


class RedisStateManager:
    """Gestor de estado compartido usando Redis."""

    def __init__(self, redis_url='redis://localhost:6378/0'):
        """
        Inicializa el gestor de estado de Redis.

        Args:
            redis_url: URL de conexión a Redis
        """
        self.redis_url = redis_url
        self._redis_client = None
        self.machine_id = None

    def _get_redis_client(self):
        """
        Obtiene el cliente de Redis (lazy initialization).

        Returns:
            redis.Redis: Cliente de Redis

        Raises:
            ConnectionError: Si no se puede conectar a Redis
        """
        if self._redis_client is None:
            try:
                self._redis_client = redis.from_url(
                    self.redis_url,
                    decode_responses=False,  # No decodificar automáticamente
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                # Verificar conexión
                self._redis_client.ping()
                print(f"[REDIS-STATE] ✅ Conectado a Redis: {self.redis_url}")
            except redis.ConnectionError as e:
                print(f"[REDIS-STATE] ❌ Error al conectar a Redis: {e}")
                raise ConnectionError(f"No se pudo conectar a Redis: {e}")

        return self._redis_client

    def set_machine_id(self, machine_id):
        """
        Configura el machine_id para este servidor.

        Args:
            machine_id: ID de la máquina
        """
        self.machine_id = machine_id
        print(f"[REDIS-STATE] Machine ID configurado: {machine_id}")

    def save_execution_state(self, execution_id, state, ttl=86400):
        """
        Guarda el estado de una ejecución en Redis.

        Args:
            execution_id: ID de la ejecución
            state: Diccionario con el estado (puede ser parcial para actualizar)
            ttl: Time to live en segundos (por defecto 24h)

        Example:
            save_execution_state('abc123', {
                'status': 'running',
                'task_id': 'xyz',
                'started_at': time.time()
            })
        """
        if not execution_id:
            print(f"[REDIS-STATE] ⚠️  execution_id vacío, no se guarda estado")
            return

        try:
            client = self._get_redis_client()
            key = f'execution:{execution_id}'

            # Convertir valores a strings para Redis
            redis_state = {}
            for k, v in state.items():
                if v is not None:
                    redis_state[k] = str(v)

            # Actualizar o crear hash
            if redis_state:
                client.hset(key, mapping=redis_state)

                # Configurar TTL
                client.expire(key, ttl)

                print(f"[REDIS-STATE] 💾 Estado guardado: {execution_id} → {state}")

        except Exception as e:
            print(f"[REDIS-STATE] ❌ Error al guardar estado: {e}")
            import traceback
            traceback.print_exc()

    def load_execution_state(self, execution_id) -> Optional[Dict]:
        """
        Carga el estado de una ejecución desde Redis.

        Args:
            execution_id: ID de la ejecución

        Returns:
            dict: Estado de la ejecución o None si no existe

        Example:
            state = load_execution_state('abc123')
            # {'status': 'running', 'task_id': 'xyz', ...}
        """
        if not execution_id:
            return None

        try:
            client = self._get_redis_client()
            key = f'execution:{execution_id}'

            # Obtener hash completo
            redis_data = client.hgetall(key)

            if not redis_data:
                return None

            # Decodificar y convertir a dict
            state = {}
            for k, v in redis_data.items():
                k_str = k.decode('utf-8') if isinstance(k, bytes) else k
                v_str = v.decode('utf-8') if isinstance(v, bytes) else v
                state[k_str] = v_str

            return state

        except Exception as e:
            print(f"[REDIS-STATE] ❌ Error al cargar estado: {e}")
            return None

    def set_server_status(self, status):
        """
        Configura el estado del servidor en Redis.

        Args:
            status: Estado del servidor ('free', 'running', 'blocked', 'closed', 'paused')
        """
        if not self.machine_id:
            print(f"[REDIS-STATE] ⚠️  machine_id no configurado, no se guarda estado del servidor")
            return

        try:
            client = self._get_redis_client()
            key = f'server:{self.machine_id}:status'

            client.set(key, status)
            print(f"[REDIS-STATE] 🖥️  Estado del servidor: {status}")

        except Exception as e:
            print(f"[REDIS-STATE] ❌ Error al guardar estado del servidor: {e}")

    def get_server_status(self) -> str:
        """
        Obtiene el estado del servidor desde Redis.

        Returns:
            str: Estado del servidor o 'free' si no existe
        """
        if not self.machine_id:
            return 'free'

        try:
            client = self._get_redis_client()
            key = f'server:{self.machine_id}:status'

            status = client.get(key)

            if status:
                status = status.decode('utf-8') if isinstance(status, bytes) else status
                return status

            return 'free'

        except Exception as e:
            print(f"[REDIS-STATE] ❌ Error al obtener estado del servidor: {e}")
            return 'free'

    def request_pause(self, execution_id):
        """
        Solicita pausar una ejecución escribiendo un flag en Redis.

        Args:
            execution_id: ID de la ejecución a pausar
        """
        if not execution_id:
            return

        try:
            client = self._get_redis_client()
            key = f'execution:{execution_id}:pause_control'

            client.hset(key, mapping={
                'pause_requested': 'true',
                'pause_requested_at': str(time.time())
            })

            # TTL de 1 hora para el control de pausa
            client.expire(key, 3600)

            print(f"[REDIS-STATE] ⏸️  Solicitud de pausa enviada: {execution_id}")

        except Exception as e:
            print(f"[REDIS-STATE] ❌ Error al solicitar pausa: {e}")

    def request_resume(self, execution_id):
        """
        Solicita reanudar una ejecución escribiendo un flag en Redis.

        Args:
            execution_id: ID de la ejecución a reanudar
        """
        if not execution_id:
            return

        try:
            client = self._get_redis_client()
            key = f'execution:{execution_id}:pause_control'

            client.hset(key, mapping={
                'resume_requested': 'true',
                'resume_requested_at': str(time.time()),
                'pause_requested': 'false'  # Limpiar solicitud de pausa
            })

            # TTL de 1 hora
            client.expire(key, 3600)

            print(f"[REDIS-STATE] ▶️  Solicitud de reanudación enviada: {execution_id}")

        except Exception as e:
            print(f"[REDIS-STATE] ❌ Error al solicitar reanudación: {e}")

    def get_pause_control(self, execution_id) -> Dict:
        """
        Obtiene el estado del control de pause/resume.

        Args:
            execution_id: ID de la ejecución

        Returns:
            dict: Estado del control con pause_requested y resume_requested

        Example:
            control = get_pause_control('abc123')
            # {'pause_requested': True, 'resume_requested': False, ...}
        """
        if not execution_id:
            return {
                'pause_requested': False,
                'resume_requested': False
            }

        try:
            client = self._get_redis_client()
            key = f'execution:{execution_id}:pause_control'

            control_data = client.hgetall(key)

            if not control_data:
                return {
                    'pause_requested': False,
                    'resume_requested': False
                }

            # Decodificar y parsear
            result = {}
            for k, v in control_data.items():
                k_str = k.decode('utf-8') if isinstance(k, bytes) else k
                v_str = v.decode('utf-8') if isinstance(v, bytes) else v

                # Convertir 'true'/'false' a bool
                if k_str in ['pause_requested', 'resume_requested']:
                    result[k_str] = v_str.lower() == 'true'
                else:
                    result[k_str] = v_str

            # Asegurar que existan las claves
            result.setdefault('pause_requested', False)
            result.setdefault('resume_requested', False)

            return result

        except Exception as e:
            print(f"[REDIS-STATE] ❌ Error al obtener control de pausa: {e}")
            return {
                'pause_requested': False,
                'resume_requested': False
            }

    def clear_pause_control(self, execution_id):
        """
        Limpia el control de pause/resume.

        Args:
            execution_id: ID de la ejecución
        """
        if not execution_id:
            return

        try:
            client = self._get_redis_client()
            key = f'execution:{execution_id}:pause_control'

            client.delete(key)
            print(f"[REDIS-STATE] 🧹 Control de pausa limpiado: {execution_id}")

        except Exception as e:
            print(f"[REDIS-STATE] ❌ Error al limpiar control de pausa: {e}")

    def mark_orphaned_executions_as_failed(self):
        """
        Marca ejecuciones huérfanas (running/paused) como fallidas.

        Se llama al iniciar el servidor para recuperar de crashes/reinicios.
        Busca ejecuciones con status 'running' o 'paused' y las marca como 'failed'.
        """
        try:
            client = self._get_redis_client()

            # Buscar todas las ejecuciones
            execution_keys = client.keys('execution:*')

            # Filtrar solo las claves principales (no :pause_control)
            execution_keys = [k.decode('utf-8') if isinstance(k, bytes) else k
                             for k in execution_keys
                             if ':pause_control' not in (k.decode('utf-8') if isinstance(k, bytes) else k)]

            orphaned_count = 0

            for key in execution_keys:
                # Obtener estado
                state_data = client.hgetall(key)

                if not state_data:
                    continue

                # Decodificar
                state = {}
                for k, v in state_data.items():
                    k_str = k.decode('utf-8') if isinstance(k, bytes) else k
                    v_str = v.decode('utf-8') if isinstance(v, bytes) else v
                    state[k_str] = v_str

                # Verificar si está huérfana (running o paused)
                status = state.get('status', '')
                if status in ['running', 'paused', 'pending']:
                    execution_id = key.replace('execution:', '')

                    # Marcar como fallida
                    client.hset(key, mapping={
                        'status': 'failed',
                        'exit_code': '-2',
                        'error': 'Execution interrupted by server restart',
                        'finished_at': str(time.time())
                    })

                    # Limpiar control de pausa
                    client.delete(f'execution:{execution_id}:pause_control')

                    orphaned_count += 1
                    print(f"[REDIS-STATE] ⚠️  Ejecución huérfana marcada como fallida: {execution_id}")

            if orphaned_count > 0:
                print(f"[REDIS-STATE] 🔄 Recuperación completada: {orphaned_count} ejecuciones huérfanas marcadas como fallidas")
            else:
                print(f"[REDIS-STATE] ✅ No se encontraron ejecuciones huérfanas")

        except Exception as e:
            print(f"[REDIS-STATE] ❌ Error al marcar ejecuciones huérfanas: {e}")
            import traceback
            traceback.print_exc()


# Instancia global del gestor de estado
redis_state = RedisStateManager()
