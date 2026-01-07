"""
Redis Manager for Robot Runner

Este módulo gestiona el ciclo de vida de Redis local para Robot Runner.
Incluye instalación, inicio, detención y verificación de estado.

Compatible con:
    - macOS: brew install redis
    - Linux: apt-get/yum install redis
    - Windows: Requiere instalación manual (Memurai o WSL)
"""
import subprocess
import platform
import os
import time
import signal
from pathlib import Path


class RedisManager:
    """Gestor de Redis local."""

    def __init__(self, redis_port=6378):
        """
        Inicializa el gestor de Redis.

        Args:
            redis_port: Puerto de Redis (por defecto 6379)
        """
        self.redis_port = redis_port
        self.redis_process = None

    def is_redis_installed(self) -> bool:
        """
        Verifica si Redis está instalado en el sistema.

        Returns:
            bool: True si Redis está instalado, False en caso contrario
        """
        try:
            # Intentar ejecutar redis-server --version
            result = subprocess.run(
                ['redis-server', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                print(f"[REDIS-MANAGER] ✅ Redis instalado: {result.stdout.strip()}")
                return True
            else:
                return False

        except (FileNotFoundError, subprocess.TimeoutExpired):
            print(f"[REDIS-MANAGER] ⚠️  Redis no está instalado")
            return False

    def install_redis(self):
        """
        Instala Redis en el sistema según la plataforma.

        Raises:
            RuntimeError: Si no se puede instalar Redis
        """
        system = platform.system()

        print(f"[REDIS-MANAGER] 📦 Instalando Redis en {system}...")

        try:
            if system == 'Darwin':  # macOS
                print(f"[REDIS-MANAGER] Usando Homebrew para instalar Redis")
                subprocess.run(['brew', 'install', 'redis'], check=True)
                print(f"[REDIS-MANAGER] ✅ Redis instalado exitosamente")

            elif system == 'Linux':
                # Detectar distribución
                try:
                    # Intentar con apt-get (Debian/Ubuntu)
                    print(f"[REDIS-MANAGER] Intentando instalar con apt-get")
                    subprocess.run(['sudo', 'apt-get', 'update'], check=True)
                    subprocess.run(['sudo', 'apt-get', 'install', '-y', 'redis-server'], check=True)
                    print(f"[REDIS-MANAGER] ✅ Redis instalado exitosamente")
                except (FileNotFoundError, subprocess.CalledProcessError):
                    # Intentar con yum (RHEL/CentOS)
                    print(f"[REDIS-MANAGER] Intentando instalar con yum")
                    subprocess.run(['sudo', 'yum', 'install', '-y', 'redis'], check=True)
                    print(f"[REDIS-MANAGER] ✅ Redis instalado exitosamente")

            elif system == 'Windows':
                raise RuntimeError(
                    "Redis no está disponible oficialmente para Windows. "
                    "Por favor instala Memurai (https://www.memurai.com/) o usa WSL."
                )

            else:
                raise RuntimeError(f"Plataforma no soportada: {system}")

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Error al instalar Redis: {e}")
        except FileNotFoundError as e:
            raise RuntimeError(f"Comando no encontrado: {e}")

    def is_redis_running(self) -> bool:
        """
        Verifica si Redis está corriendo.

        Returns:
            bool: True si Redis está corriendo, False en caso contrario
        """
        try:
            # Intentar conectar a Redis
            import redis
            client = redis.Redis(host='localhost', port=self.redis_port, socket_connect_timeout=2)
            client.ping()
            return True

        except Exception:
            return False

    def start_redis(self):
        """
        Inicia Redis como subprocess en el puerto configurado.

        Si Redis ya está corriendo, no hace nada.

        Raises:
            RuntimeError: Si no se puede iniciar Redis
        """
        # Verificar si ya está corriendo
        if self.is_redis_running():
            print(f"[REDIS-MANAGER] ✅ Redis ya está corriendo en puerto {self.redis_port}")
            return

        print(f"[REDIS-MANAGER] 🚀 Iniciando Redis en puerto {self.redis_port}...")

        try:
            # Configurar archivo de configuración temporal si es necesario
            # Por ahora, usar configuración por defecto

            # Iniciar Redis como subprocess
            self.redis_process = subprocess.Popen(
                ['redis-server', '--port', str(self.redis_port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True  # Nuevo grupo de procesos
            )

            # Esperar a que inicie (máximo 5 segundos)
            for i in range(10):
                time.sleep(0.5)
                if self.is_redis_running():
                    print(f"[REDIS-MANAGER] ✅ Redis iniciado exitosamente (PID: {self.redis_process.pid})")
                    return

            # Si llegamos aquí, no inició en el timeout
            raise RuntimeError("Redis no inició en el tiempo esperado")

        except FileNotFoundError:
            raise RuntimeError(
                "redis-server no encontrado. Por favor instala Redis primero."
            )
        except Exception as e:
            raise RuntimeError(f"Error al iniciar Redis: {e}")

    def stop_redis(self):
        """
        Detiene el proceso de Redis si fue iniciado por este manager.

        Returns:
            bool: True si se detuvo exitosamente, False si no había proceso
        """
        if self.redis_process is None:
            print(f"[REDIS-MANAGER] ⚠️  No hay proceso de Redis gestionado por este manager")
            return False

        print(f"[REDIS-MANAGER] 🛑 Deteniendo Redis...")

        try:
            # Enviar SIGTERM para terminación grácil
            self.redis_process.terminate()

            # Esperar a que termine (timeout de 5 segundos)
            try:
                self.redis_process.wait(timeout=5)
                print(f"[REDIS-MANAGER] ✅ Redis detenido exitosamente")
            except subprocess.TimeoutExpired:
                # Si no terminó, forzar
                print(f"[REDIS-MANAGER] ⚠️  Redis no terminó grácilmente, forzando...")
                self.redis_process.kill()
                self.redis_process.wait()
                print(f"[REDIS-MANAGER] ✅ Redis forzadamente detenido")

            self.redis_process = None
            return True

        except Exception as e:
            print(f"[REDIS-MANAGER] ❌ Error al detener Redis: {e}")
            return False

    def ensure_redis_running(self):
        """
        Asegura que Redis esté corriendo.

        Si no está instalado, intenta instalarlo.
        Si no está corriendo, lo inicia.

        Raises:
            RuntimeError: Si no se puede asegurar que Redis esté corriendo
        """
        print(f"[REDIS-MANAGER] 🔍 Verificando Redis...")

        # Verificar instalación
        if not self.is_redis_installed():
            print(f"[REDIS-MANAGER] ⚠️  Redis no está instalado")

            # En sistemas que soportan instalación automática, intentar instalar
            system = platform.system()
            if system in ['Darwin', 'Linux']:
                print(f"[REDIS-MANAGER] Intentando instalar Redis automáticamente...")
                try:
                    self.install_redis()
                except Exception as e:
                    raise RuntimeError(
                        f"No se pudo instalar Redis automáticamente: {e}\n"
                        f"Por favor instala Redis manualmente."
                    )
            else:
                raise RuntimeError(
                    "Redis no está instalado. Por favor instálalo manualmente:\n"
                    "- macOS: brew install redis\n"
                    "- Linux: sudo apt-get install redis-server (o yum install redis)\n"
                    "- Windows: Instala Memurai (https://www.memurai.com/) o usa WSL"
                )

        # Verificar si está corriendo
        if not self.is_redis_running():
            print(f"[REDIS-MANAGER] Redis no está corriendo, iniciando...")
            try:
                self.start_redis()
            except Exception as e:
                raise RuntimeError(f"No se pudo iniciar Redis: {e}")

        print(f"[REDIS-MANAGER] ✅ Redis está listo en puerto {self.redis_port}")

    def get_redis_info(self):
        """
        Obtiene información sobre el estado de Redis.

        Returns:
            dict: Información de Redis o None si no está disponible
        """
        if not self.is_redis_running():
            return None

        try:
            import redis
            client = redis.Redis(host='localhost', port=self.redis_port, socket_connect_timeout=2)
            info = client.info()

            return {
                'version': info.get('redis_version'),
                'uptime_seconds': info.get('uptime_in_seconds'),
                'connected_clients': info.get('connected_clients'),
                'used_memory_human': info.get('used_memory_human'),
                'port': self.redis_port
            }

        except Exception as e:
            print(f"[REDIS-MANAGER] ❌ Error al obtener info de Redis: {e}")
            return None


# Instancia global del gestor de Redis
redis_manager = RedisManager()
