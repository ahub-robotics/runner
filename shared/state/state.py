"""
State Manager for Robot Runner (Backend-Agnostic)

Este módulo gestiona el estado compartido de ejecuciones usando backends abstractos.
Soporta Redis (Linux/macOS) y SQLite (Windows) automáticamente.

Estructura de claves:
    - execution:{id} (Hash): Estado de la ejecución
    - execution:{id}:pause_control (Hash): Control de pause/resume
    - server:{machine_id}:status (String): Estado del servidor
"""
import time
from typing import Dict, Optional
from .backends import get_state_backend


class StateManager:
    """Gestor de estado compartido usando backends abstractos (Redis o SQLite)."""

    def __init__(self, backend=None):
        """
        Inicializa el gestor de estado.

        Args:
            backend: StateBackend instance (optional, will auto-detect if not provided)
        """
        self.backend = backend or get_state_backend()
        self.machine_id = None

        # Verify connectivity
        if not self.backend.ping():
            raise ConnectionError("No se pudo conectar al backend de estado")

        print(f"[STATE-MANAGER] ✅ Inicializado con backend: {type(self.backend).__name__}")

    def set_machine_id(self, machine_id):
        """
        Configura el machine_id para este servidor.

        Args:
            machine_id: ID de la máquina
        """
        self.machine_id = machine_id
        print(f"[STATE-MANAGER] Machine ID configurado: {machine_id}")

    def save_execution_state(self, execution_id, state, ttl=86400):
        """
        Guarda el estado de una ejecución.

        Args:
            execution_id: ID de la ejecución
            state: Diccionario con el estado (puede ser parcial para actualizar)
            ttl: Time to live en segundos (por defecto 24h) - NO IMPLEMENTED YET

        Example:
            save_execution_state('abc123', {
                'status': 'running',
                'task_id': 'xyz',
                'started_at': time.time()
            })
        """
        if not execution_id:
            print(f"[STATE-MANAGER] ⚠️  execution_id vacío, no se guarda estado")
            return

        try:
            key = f'execution:{execution_id}'

            # Convertir valores a strings
            string_state = {}
            for k, v in state.items():
                if v is not None:
                    string_state[k] = str(v)

            # Guardar en backend
            if string_state:
                self.backend.hset(key, string_state)
                print(f"[STATE-MANAGER] 💾 Estado guardado: {execution_id} → {list(string_state.keys())}")
        except Exception as e:
            print(f"[STATE-MANAGER] ❌ Error guardando estado: {e}")

    def get_execution_state(self, execution_id) -> Dict:
        """
        Obtiene el estado de una ejecución.

        Args:
            execution_id: ID de la ejecución

        Returns:
            dict: Estado de la ejecución o dict vacío si no existe

        Example:
            state = get_execution_state('abc123')
            if state:
                print(f"Status: {state['status']}")
        """
        if not execution_id:
            return {}

        try:
            key = f'execution:{execution_id}'
            state_data = self.backend.hgetall(key)

            if not state_data:
                return {}

            # Convertir bytes a strings si es necesario
            result = {}
            for k, v in state_data.items():
                key_str = k.decode('utf-8') if isinstance(k, bytes) else k
                val_str = v.decode('utf-8') if isinstance(v, bytes) else v
                result[key_str] = val_str

            return result

        except Exception as e:
            print(f"[STATE-MANAGER] ❌ Error obteniendo estado de {execution_id}: {e}")
            return {}

    def set_server_status(self, status):
        """
        Establece el estado del servidor.

        Args:
            status: Estado del servidor ('free', 'busy', 'paused', etc.)
        """
        if not self.machine_id:
            print(f"[STATE-MANAGER] ⚠️  machine_id no configurado, no se puede guardar status")
            return

        try:
            key = f'server:{self.machine_id}:status'
            self.backend.set(key, status)
            print(f"[STATE-MANAGER] 🖥️  Estado del servidor: {status}")
        except Exception as e:
            print(f"[STATE-MANAGER] ❌ Error guardando status del servidor: {e}")

    def get_server_status(self) -> str:
        """
        Obtiene el estado del servidor.

        Returns:
            str: Estado del servidor o 'unknown' si no está configurado
        """
        if not self.machine_id:
            return 'unknown'

        try:
            key = f'server:{self.machine_id}:status'
            status = self.backend.get(key)

            if status:
                status_str = status.decode('utf-8') if isinstance(status, bytes) else status
                return status_str
            return 'unknown'

        except Exception as e:
            print(f"[STATE-MANAGER] ❌ Error obteniendo status del servidor: {e}")
            return 'unknown'

    def set_pause_control(self, execution_id, pause_requested=False, resume_requested=False):
        """
        Establece el control de pause/resume para una ejecución.

        Args:
            execution_id: ID de la ejecución
            pause_requested: Si se solicitó pausar
            resume_requested: Si se solicitó reanudar
        """
        if not execution_id:
            return

        try:
            key = f'execution:{execution_id}:pause_control'
            self.backend.hset(key, {
                'pause_requested': str(pause_requested).lower(),
                'resume_requested': str(resume_requested).lower(),
                'updated_at': str(time.time())
            })
        except Exception as e:
            print(f"[STATE-MANAGER] ❌ Error guardando pause control: {e}")

    def request_pause(self, execution_id):
        """
        Solicita pausar una ejecución.

        Args:
            execution_id: ID de la ejecución
        """
        self.set_pause_control(execution_id, pause_requested=True, resume_requested=False)

    def request_resume(self, execution_id):
        """
        Solicita reanudar una ejecución.

        Args:
            execution_id: ID de la ejecución
        """
        self.set_pause_control(execution_id, pause_requested=False, resume_requested=True)

    def get_pause_control(self, execution_id) -> Dict:
        """
        Obtiene el estado del control de pause/resume.

        Args:
            execution_id: ID de la ejecución

        Returns:
            dict: {'pause_requested': bool, 'resume_requested': bool}
        """
        if not execution_id:
            return {'pause_requested': False, 'resume_requested': False}

        try:
            key = f'execution:{execution_id}:pause_control'
            control_data = self.backend.hgetall(key)

            if not control_data:
                return {'pause_requested': False, 'resume_requested': False}

            # Convertir strings a booleans
            result = {}
            for k, v in control_data.items():
                key_str = k.decode('utf-8') if isinstance(k, bytes) else k
                val_str = v.decode('utf-8') if isinstance(v, bytes) else v
                result[key_str] = val_str

            # Parsear booleans
            result.setdefault('pause_requested', False)
            result.setdefault('resume_requested', False)

            if isinstance(result['pause_requested'], str):
                result['pause_requested'] = result['pause_requested'].lower() == 'true'
            if isinstance(result['resume_requested'], str):
                result['resume_requested'] = result['resume_requested'].lower() == 'true'

            return result

        except Exception as e:
            print(f"[STATE-MANAGER] ❌ Error obteniendo pause control: {e}")
            return {'pause_requested': False, 'resume_requested': False}

    def clear_pause_control(self, execution_id):
        """
        Limpia el control de pause/resume de una ejecución.

        Args:
            execution_id: ID de la ejecución
        """
        if not execution_id:
            return

        try:
            key = f'execution:{execution_id}:pause_control'
            self.backend.delete(key)
        except Exception as e:
            print(f"[STATE-MANAGER] ❌ Error limpiando pause control: {e}")

    def mark_orphaned_executions_as_failed(self):
        """
        Marca como fallidas todas las ejecuciones en estado 'running' o 'paused'.

        Se usa al iniciar el servidor para recuperarse de crashes.
        """
        try:
            # Buscar todas las claves de ejecuciones
            execution_keys = self.backend.keys('execution:*')

            # Filtrar solo las claves de estado (no pause_control)
            state_keys = [k for k in execution_keys if not k.endswith(':pause_control')]

            failed_count = 0
            for key in state_keys:
                state_data = self.backend.hgetall(key)

                if not state_data:
                    continue

                # Convertir bytes a strings
                state = {}
                for k, v in state_data.items():
                    key_str = k.decode('utf-8') if isinstance(k, bytes) else k
                    val_str = v.decode('utf-8') if isinstance(v, bytes) else v
                    state[key_str] = val_str

                status = state.get('status', '')

                if status in ['running', 'paused']:
                    # Marcar como fallida
                    execution_id = key.replace('execution:', '')
                    self.backend.hset(key, {
                        'status': 'failed',
                        'error': 'Server restarted while execution was running'
                    })
                    # Limpiar pause control si existía
                    self.backend.delete(f'execution:{execution_id}:pause_control')
                    failed_count += 1

            if failed_count > 0:
                print(f"[STATE-MANAGER] ⚠️  Marcadas {failed_count} ejecuciones huérfanas como fallidas")
            else:
                print(f"[STATE-MANAGER] ✅ No se encontraron ejecuciones huérfanas")

        except Exception as e:
            print(f"[STATE-MANAGER] ❌ Error marcando ejecuciones huérfanas: {e}")


# Global singleton instance
_state_manager = None


def get_state_manager() -> StateManager:
    """
    Obtiene la instancia global del StateManager (singleton).

    Returns:
        StateManager: Instancia única del gestor de estado
    """
    global _state_manager

    if _state_manager is None:
        _state_manager = StateManager()

    return _state_manager


# Mantener compatibilidad con código existente
redis_state = get_state_manager()
