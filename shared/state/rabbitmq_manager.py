"""
RabbitMQ Manager for Robot Runner

Este módulo gestiona el ciclo de vida de RabbitMQ para Robot Runner.
Incluye verificación de instalación, inicio y detención del servicio.

Compatible con:
    - macOS: brew services start/stop rabbitmq
    - Linux: systemctl start/stop rabbitmq-server
    - Windows: net start/stop RabbitMQ
"""
import subprocess
import platform
import socket
import time


class RabbitMQManager:
    """Gestor de RabbitMQ."""

    def __init__(self, host='localhost', port=5672):
        """
        Inicializa el gestor de RabbitMQ.

        Args:
            host: Host de RabbitMQ (por defecto localhost)
            port: Puerto de RabbitMQ (por defecto 5672)
        """
        self.host = host
        self.port = port

    def is_rabbitmq_installed(self) -> bool:
        """
        Verifica si RabbitMQ está instalado en el sistema.

        Returns:
            bool: True si RabbitMQ está instalado, False en caso contrario
        """
        system = platform.system()

        try:
            if system == 'Darwin':  # macOS
                # Verificar si RabbitMQ está instalado con Homebrew
                result = subprocess.run(
                    ['brew', 'list', 'rabbitmq'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    print(f"[RABBITMQ-MANAGER] ✅ RabbitMQ instalado via Homebrew")
                    return True

            elif system == 'Linux':
                # Verificar si rabbitmqctl está disponible
                result = subprocess.run(
                    ['which', 'rabbitmqctl'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    print(f"[RABBITMQ-MANAGER] ✅ RabbitMQ instalado: {result.stdout.strip()}")
                    return True

            elif system == 'Windows':
                # Verificar si el servicio de RabbitMQ existe
                result = subprocess.run(
                    ['sc', 'query', 'RabbitMQ'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    print(f"[RABBITMQ-MANAGER] ✅ RabbitMQ instalado como servicio")
                    return True

            print(f"[RABBITMQ-MANAGER] ⚠️  RabbitMQ no está instalado")
            return False

        except (FileNotFoundError, subprocess.TimeoutExpired):
            print(f"[RABBITMQ-MANAGER] ⚠️  No se pudo verificar instalación de RabbitMQ")
            return False

    def is_rabbitmq_running(self) -> bool:
        """
        Verifica si RabbitMQ está corriendo.

        Returns:
            bool: True si RabbitMQ está corriendo, False en caso contrario
        """
        try:
            # Intentar conectar a RabbitMQ via TCP
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((self.host, self.port))
            sock.close()
            return result == 0

        except Exception:
            return False

    def start_rabbitmq(self):
        """
        Inicia RabbitMQ usando el gestor de servicios apropiado.

        Si RabbitMQ ya está corriendo, no hace nada.

        Raises:
            RuntimeError: Si no se puede iniciar RabbitMQ
        """
        # Verificar si ya está corriendo
        if self.is_rabbitmq_running():
            print(f"[RABBITMQ-MANAGER] ✅ RabbitMQ ya está corriendo en {self.host}:{self.port}")
            return

        print(f"[RABBITMQ-MANAGER] 🚀 Iniciando RabbitMQ...")

        system = platform.system()

        try:
            if system == 'Darwin':  # macOS
                # Iniciar con Homebrew services
                subprocess.run(
                    ['brew', 'services', 'start', 'rabbitmq'],
                    check=True,
                    capture_output=True,
                    text=True
                )

            elif system == 'Linux':
                # Intentar con systemctl
                try:
                    subprocess.run(
                        ['sudo', 'systemctl', 'start', 'rabbitmq-server'],
                        check=True,
                        capture_output=True,
                        text=True
                    )
                except (FileNotFoundError, subprocess.CalledProcessError):
                    # Intentar con service
                    subprocess.run(
                        ['sudo', 'service', 'rabbitmq-server', 'start'],
                        check=True,
                        capture_output=True,
                        text=True
                    )

            elif system == 'Windows':
                # Iniciar servicio de Windows
                subprocess.run(
                    ['net', 'start', 'RabbitMQ'],
                    check=True,
                    capture_output=True,
                    text=True
                )

            # Esperar a que inicie (máximo 10 segundos)
            for i in range(20):
                time.sleep(0.5)
                if self.is_rabbitmq_running():
                    print(f"[RABBITMQ-MANAGER] ✅ RabbitMQ iniciado exitosamente")
                    return

            # Si llegamos aquí, no inició en el timeout
            raise RuntimeError("RabbitMQ no inició en el tiempo esperado")

        except FileNotFoundError:
            raise RuntimeError(
                "No se encontró el comando para iniciar RabbitMQ. "
                "Por favor instala RabbitMQ primero."
            )
        except subprocess.CalledProcessError as e:
            # Extraer mensaje de error si está disponible
            error_msg = e.stderr if e.stderr else str(e)
            raise RuntimeError(f"Error al iniciar RabbitMQ: {error_msg}")
        except Exception as e:
            raise RuntimeError(f"Error inesperado al iniciar RabbitMQ: {e}")

    def stop_rabbitmq(self):
        """
        Detiene RabbitMQ usando el gestor de servicios apropiado.

        Returns:
            bool: True si se detuvo exitosamente, False si no estaba corriendo
        """
        if not self.is_rabbitmq_running():
            print(f"[RABBITMQ-MANAGER] ⚠️  RabbitMQ no está corriendo")
            return False

        print(f"[RABBITMQ-MANAGER] 🛑 Deteniendo RabbitMQ...")

        system = platform.system()

        try:
            if system == 'Darwin':  # macOS
                subprocess.run(
                    ['brew', 'services', 'stop', 'rabbitmq'],
                    check=True,
                    capture_output=True,
                    text=True
                )

            elif system == 'Linux':
                try:
                    subprocess.run(
                        ['sudo', 'systemctl', 'stop', 'rabbitmq-server'],
                        check=True,
                        capture_output=True,
                        text=True
                    )
                except (FileNotFoundError, subprocess.CalledProcessError):
                    subprocess.run(
                        ['sudo', 'service', 'rabbitmq-server', 'stop'],
                        check=True,
                        capture_output=True,
                        text=True
                    )

            elif system == 'Windows':
                subprocess.run(
                    ['net', 'stop', 'RabbitMQ'],
                    check=True,
                    capture_output=True,
                    text=True
                )

            print(f"[RABBITMQ-MANAGER] ✅ RabbitMQ detenido exitosamente")
            return True

        except Exception as e:
            print(f"[RABBITMQ-MANAGER] ❌ Error al detener RabbitMQ: {e}")
            return False

    def ensure_rabbitmq_running(self):
        """
        Asegura que RabbitMQ esté corriendo.

        Si no está instalado, muestra instrucciones de instalación.
        Si no está corriendo, lo inicia.

        Raises:
            RuntimeError: Si no se puede asegurar que RabbitMQ esté corriendo
        """
        print(f"[RABBITMQ-MANAGER] 🔍 Verificando RabbitMQ...")

        # Verificar instalación
        if not self.is_rabbitmq_installed():
            system = platform.system()

            if system == 'Darwin':
                error_msg = (
                    "RabbitMQ no está instalado.\n"
                    "Para instalarlo en macOS:\n"
                    "  brew install rabbitmq\n"
                    "  brew services start rabbitmq"
                )
            elif system == 'Linux':
                error_msg = (
                    "RabbitMQ no está instalado.\n"
                    "Para instalarlo en Linux:\n"
                    "  sudo apt-get update\n"
                    "  sudo apt-get install rabbitmq-server\n"
                    "  sudo systemctl start rabbitmq-server"
                )
            elif system == 'Windows':
                error_msg = (
                    "RabbitMQ no está instalado.\n"
                    "Para instalarlo en Windows:\n"
                    "  Descarga desde: https://www.rabbitmq.com/download.html\n"
                    "  O usa Chocolatey: choco install rabbitmq"
                )
            else:
                error_msg = f"RabbitMQ no está instalado (sistema: {system})"

            raise RuntimeError(error_msg)

        # Verificar si está corriendo
        if not self.is_rabbitmq_running():
            print(f"[RABBITMQ-MANAGER] RabbitMQ no está corriendo, iniciando...")
            try:
                self.start_rabbitmq()
            except Exception as e:
                raise RuntimeError(f"No se pudo iniciar RabbitMQ: {e}")

        print(f"[RABBITMQ-MANAGER] ✅ RabbitMQ está listo en {self.host}:{self.port}")

    def get_rabbitmq_status(self):
        """
        Obtiene información sobre el estado de RabbitMQ.

        Returns:
            dict: Información de RabbitMQ o None si no está disponible
        """
        if not self.is_rabbitmq_running():
            return None

        system = platform.system()

        try:
            if system in ['Darwin', 'Linux']:
                # Intentar obtener status con rabbitmqctl
                result = subprocess.run(
                    ['rabbitmqctl', 'status'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if result.returncode == 0:
                    return {
                        'running': True,
                        'host': self.host,
                        'port': self.port,
                        'status': 'healthy'
                    }

            return {
                'running': True,
                'host': self.host,
                'port': self.port,
                'status': 'unknown'
            }

        except Exception as e:
            print(f"[RABBITMQ-MANAGER] ❌ Error al obtener status de RabbitMQ: {e}")
            return None


# Instancia global del gestor de RabbitMQ
rabbitmq_manager = RabbitMQManager()