"""
Robot Runner Server - Wrapper del Runner

Esta clase extiende Runner y proporciona métodos de alto nivel para controlar
la ejecución del robot de manera multiplataforma.

Compatible con Windows, Linux y macOS.
"""
import json
import threading
import os
from pathlib import Path

from .runner import Runner


class Server(Runner):
    def __init__(self, kwargs):
        """
        Inicializa el servidor del robot.

        Args:
            kwargs: Diccionario con configuración (url, token, machine_id, etc.)
        """
        super().__init__(**kwargs)
        self.data = None
        self.thread = None
        self.status = "free"
        self.execution_id = None
        self.last_exit_code = None
        self._status_lock = threading.Lock()  # Lock para sincronizar cambios de estado

        # State manager (funciona con Redis o SQLite según el sistema)
        from shared.state.state import get_state_manager
        self.state_manager = get_state_manager()
        self.state_manager.set_machine_id(self.machine_id)

    def change_status(self, new_status, notify_remote=True, execution_id=None):
        """
        Cambia el estado del servidor de forma thread-safe y opcionalmente notifica al servidor remoto.

        Args:
            new_status (str): Nuevo estado ('free', 'closed', 'running', 'blocked', 'paused')
            notify_remote (bool): Si True, notifica al servidor remoto del cambio
            execution_id (str, optional): ID de ejecución asociado al cambio de estado

        Returns:
            bool: True si la notificación fue exitosa o no se requirió, False en caso de error
        """
        with self._status_lock:
            old_status = self.status

            # Cambiar estado local
            self.status = new_status

            # Gestionar execution_id según el estado
            if new_status == "running" and execution_id:
                self.execution_id = execution_id
                self.last_exit_code = None  # Reset exit code al iniciar nueva ejecución
                print(f"[STATE] Starting execution: {execution_id}")
            elif new_status in ["free", "closed"] and old_status == "running":
                # Limpiar execution_id cuando termina la ejecución
                print(f"[STATE] Execution ended: {self.execution_id} (exit code: {self.last_exit_code})")
                # NO limpiar execution_id ni last_exit_code aquí para permitir consultas posteriores

            print(f"[STATE] Status: {old_status} → {new_status}")

            # Guardar estado en Redis (reemplaza archivo JSON)
            self.state_manager.set_server_status(new_status)

            # IMPORTANTE: Solo guardar estado de ejecución cuando cambia a "running"
            # NO sobrescribir estado de ejecución cuando el servidor cambia a "free"
            # (el estado de la ejecución se maneja por separado en tasks.py)
            if execution_id and new_status == "running":
                self.state_manager.save_execution_state(execution_id, {
                    'status': new_status
                })

        # Notificar al servidor remoto si se solicita (fuera del lock)
        if notify_remote:
            try:
                self.set_machine_ip(status=new_status)
                print(f"[STATE] ✅ Notified remote server: {new_status}")
                return True
            except Exception as e:
                print(f"[STATE] ⚠️  Failed to notify remote server: {e}")
                return False

        return True

    def get_status(self):
        """
        Obtiene el estado actual de forma thread-safe.

        Returns:
            str: Estado actual del servidor
        """
        with self._status_lock:
            return self.status

    def set_execution_result(self, exit_code):
        """
        Guarda el exit code de una ejecución terminada.

        Args:
            exit_code (int): Código de salida del proceso
        """
        with self._status_lock:
            self.last_exit_code = exit_code
            print(f"[STATE] Execution result saved: exit_code={exit_code} (execution_id={self.execution_id})")

            # Guardar en Redis (reemplaza archivo JSON)
            if self.execution_id:
                self.state_manager.save_execution_state(self.execution_id, {
                    'exit_code': exit_code
                })

    def clear_execution_data(self):
        """
        Limpia los datos de ejecución (execution_id y exit_code).
        Útil para preparar una nueva ejecución.
        """
        with self._status_lock:
            print(f"[STATE] Clearing execution data: {self.execution_id}")
            self.execution_id = None
            self.last_exit_code = None

    def run(self, data):
        """
        Ejecuta un robot con los datos proporcionados.

        Args:
            data: Diccionario con información de ejecución (robot, execution, branch, params)

        Nota: Esta función es bloqueante y ejecuta el robot de forma síncrona.
        """
        print(f"[RUN] Iniciando ejecución del robot")
        print(f"[RUN] - Execution ID: {self.execution_id}")

        try:
            print(f"[RUN] Paso 1: Guardando datos")
            self.data = data

            print(f"[RUN] Paso 2: Configurando robot")
            self.set_robot(self.data)

            print(f"[RUN] Paso 3: Enviando log inicial")
            self.send_log("Execution Started")

            print(f"[RUN] Paso 4: Copiando repositorio")
            self.copy_repo()

            print(f"[RUN] Paso 5: Ejecutando robot")
            self.run_robot()

            print(f"[RUN] Paso 6: Obteniendo exit code")
            # Obtener exit code guardado por run_robot()
            # run_robot() guarda el exit code en self.last_returncode antes de limpiar el proceso
            if hasattr(self, 'last_returncode') and self.last_returncode is not None:
                exit_code = self.last_returncode
                print(f"[RUN] - Exit code obtenido desde last_returncode: {exit_code}")
            elif self.run_robot_process:
                # Fallback: intentar obtener del proceso directamente
                returncode = self.run_robot_process.poll()
                if returncode is not None:
                    exit_code = returncode
                    print(f"[RUN] - Exit code obtenido desde proceso: {exit_code}")
                else:
                    print(f"[RUN] ⚠️  Proceso sin returncode disponible, asumiendo error")
                    exit_code = 1  # Error por defecto
            else:
                print(f"[RUN] ⚠️  No se pudo obtener exit code, asumiendo error")
                exit_code = 1  # Error por defecto

            print(f"[RUN] Paso 7: Guardando resultado (exit_code={exit_code})")
            # Guardar resultado
            self.set_execution_result(exit_code)

            print(f"[RUN] Paso 8: Cambiando estado a free y notificando al servidor remoto")
            # Cambiar estado a free y notificar al orquestador
            self.change_status("free", notify_remote=True)

            print(f"[RUN] ✅ Ejecución completada exitosamente")

        except Exception as e:
            print(f"[RUN] ❌ Error durante ejecución: {e}")
            import traceback
            traceback.print_exc()

            print(f"[RUN] Guardando exit code de error")
            self.set_execution_result(1)  # Exit code 1 = error

            print(f"[RUN] Cambiando estado a free y notificando al servidor remoto")
            self.change_status("free", notify_remote=True)

            raise

    def pause(self):
        """
        Solicita pausar la ejecución actual del robot escribiendo un flag en Redis.

        El loop de ejecución en robot.py detectará este flag y pausará el proceso.
        Multiplataforma: Funciona en Windows, Linux y macOS usando psutil.
        """
        print(f"[SERVER] Solicitando pausa: {self.execution_id}")

        if self.execution_id:
            # Solicitar pausa en Redis (el loop en robot.py lo detectará)
            self.state_manager.request_pause(self.execution_id)

            # Actualizar estado en Redis
            self.state_manager.set_server_status("paused")
            self.state_manager.save_execution_state(self.execution_id, {
                'status': 'paused'
            })

            # Actualizar estado local
            self.status = "paused"

    def resume(self):
        """
        Solicita reanudar la ejecución pausada del robot escribiendo un flag en Redis.

        El loop de ejecución en robot.py detectará este flag y reanudará el proceso.
        Multiplataforma: Funciona en Windows, Linux y macOS usando psutil.
        """
        print(f"[SERVER] Solicitando reanudación: {self.execution_id}")

        if self.execution_id:
            # Solicitar reanudación en Redis (el loop en robot.py lo detectará)
            self.state_manager.request_resume(self.execution_id)

            # Actualizar estado en Redis
            self.state_manager.set_server_status("running")
            self.state_manager.save_execution_state(self.execution_id, {
                'status': 'running'
            })

            # Actualizar estado local
            self.status = "running"

    def stop(self):
        """
        Detiene la ejecución actual del robot.

        Multiplataforma: Funciona en Windows, Linux y macOS usando psutil.
        Implementa terminación grácil seguida de terminación forzada si es necesario.

        Nota: Si hay un error al detener, se captura silenciosamente y se imprime
        un mensaje. El estado se actualiza a "free" independientemente del resultado.
        """
        try:
            self.stop_execution()

            # Guardar exit code como "stopped" (código especial o usar el del proceso)
            if self.run_robot_process:
                exit_code = self.run_robot_process.poll()
                if exit_code is not None:
                    self.set_execution_result(exit_code)
                else:
                    self.set_execution_result(-1)  # Código especial para "stopped manually"

            self.change_status("free", notify_remote=True)

        except Exception as e:
            print(f"Unable to stop execution: {e}")
            self.change_status("free", notify_remote=True)
