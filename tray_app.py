#!/usr/bin/env python3
"""
================================================================================
Robot Runner - System Tray Application
================================================================================

Aplicación de bandeja del sistema para gestionar el servidor Robot Runner.

Características:
    - Iniciar/detener el servidor desde el tray
    - Ver estado del servidor en tiempo real
    - Acceder a logs
    - Abrir interfaz web
    - Iconos que cambian según el estado

Uso:
    python tray_app.py

Requisitos:
    pip install pystray pillow

================================================================================
"""

import os
import sys
import time
import subprocess
import threading
import webbrowser
from pathlib import Path
from PIL import Image, ImageDraw

try:
    import pystray
    from pystray import MenuItem as item
except ImportError:
    print("❌ Error: pystray no está instalado")
    print("   Instalar con: pip install pystray")
    sys.exit(1)

# Directorio del proyecto
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# Importar módulos locales
from scripts.kill_gunicorn import find_gunicorn_processes, kill_process
from src.config import get_config_data


class RobotRunnerTray:
    """Aplicación de System Tray para Robot Runner."""

    def __init__(self):
        """Inicializa la aplicación del tray."""
        self.icon = None
        self.server_process = None
        self.config = get_config_data()
        self.port = self.config.get('port', 5055)
        self.server_url = f"https://{self.config.get('ip', "0.0.0.0")}:{self.port}"

        # Estado
        self.is_running = False
        self.check_initial_status()

    def check_initial_status(self):
        """Verifica el estado inicial del servidor."""
        # Verificar si hay un proceso escuchando en NUESTRO puerto específico
        try:
            result = subprocess.run(
                ['lsof', '-t', '-i', f':{self.port}', '-sTCP:LISTEN'],
                capture_output=True,
                text=True,
                timeout=5
            )
            pids = [int(pid) for pid in result.stdout.strip().split('\n') if pid]
            self.is_running = len(pids) > 0

            # if self.is_running:
            #     print(f"✓ Detectado servidor corriendo en puerto {self.port} (PIDs: {', '.join(map(str, pids))})")
            # else:
            #     print(f"⚠️  No hay servidor corriendo en puerto {self.port}")

        except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
            self.is_running = False
            # print(f"⚠️  No se pudo verificar el estado del servidor en puerto {self.port}")

    def create_icon(self, color='red'):
        """
        Crea un icono para el tray usando el logo blanco con un círculo indicador de estado.

        Args:
            color (str): Color del indicador ('green' = running, 'red' = stopped, 'yellow' = starting)

        Returns:
            PIL.Image: Imagen del icono con fondo transparente
        """
        # Definir colores según el estado
        if color == 'green':
            status_color = (46, 204, 113)  # Verde
        elif color == 'yellow':
            status_color = (241, 196, 15)  # Amarillo
        else:
            status_color = (231, 76, 60)   # Rojo

        try:
            # Intentar cargar el logo de la aplicación
            logo_path = os.path.join(PROJECT_ROOT, 'static', 'images', 'logo.png')
            logo = Image.open(logo_path)

            # Convertir a RGBA si no lo es
            if logo.mode != 'RGBA':
                logo = logo.convert('RGBA')

            # Redimensionar el logo a 64x64 manteniendo aspecto
            logo.thumbnail((64, 64), Image.Resampling.LANCZOS)

            # Separar los canales RGBA
            r, g, b, alpha = logo.split()

            # Convertir a blanco manteniendo la transparencia
            white_logo = Image.new('RGBA', logo.size)
            white_data = white_logo.load()

            # Aplicar blanco a todas las partes no transparentes
            for y in range(logo.size[1]):
                for x in range(logo.size[0]):
                    alpha_val = alpha.getpixel((x, y))
                    # Mantener el canal alfa, pero hacer todo blanco
                    white_data[x, y] = (255, 255, 255, alpha_val)

            # Crear imagen base con fondo transparente
            icon = Image.new('RGBA', (64, 64), (0, 0, 0, 0))

            # Centrar el logo blanco en el icono
            logo_x = (64 - white_logo.width) // 2
            logo_y = (64 - white_logo.height) // 2
            icon.paste(white_logo, (logo_x, logo_y), white_logo)

            # Agregar círculo indicador de estado en la esquina inferior derecha
            dc = ImageDraw.Draw(icon)
            indicator_size = 14
            indicator_x = 64 - indicator_size - 4
            indicator_y = 64 - indicator_size - 4

            # Círculo con borde blanco
            dc.ellipse(
                [indicator_x - 2, indicator_y - 2,
                 indicator_x + indicator_size + 2, indicator_y + indicator_size + 2],
                fill='white'
            )
            # Círculo del color de estado
            dc.ellipse(
                [indicator_x, indicator_y,
                 indicator_x + indicator_size, indicator_y + indicator_size],
                fill=status_color
            )

            return icon

        except Exception as e:
            # Fallback: crear icono simple si no se puede cargar el logo
            print(f"⚠️  No se pudo cargar el logo: {e}")
            print(f"   Usando icono simple como fallback")

            # Crear icono simple con fondo transparente
            icon = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
            dc = ImageDraw.Draw(icon)

            # Dibujar círculo blanco
            dc.ellipse([8, 8, 56, 56], fill='white', outline='white')

            # Dibujar letra "R" en el centro
            dc.text((22, 16), "R", fill='black')

            # Agregar indicador de estado
            indicator_size = 14
            indicator_x = 64 - indicator_size - 4
            indicator_y = 64 - indicator_size - 4

            dc.ellipse(
                [indicator_x - 2, indicator_y - 2,
                 indicator_x + indicator_size + 2, indicator_y + indicator_size + 2],
                fill='white'
            )
            dc.ellipse(
                [indicator_x, indicator_y,
                 indicator_x + indicator_size, indicator_y + indicator_size],
                fill=status_color
            )

            return icon

    def update_icon(self):
        """Actualiza el icono según el estado del servidor."""
        if self.icon:
            if self.is_running:
                self.icon.icon = self.create_icon('green')
                self.icon.title = "Robot Runner (Running)"
            else:
                self.icon.icon = self.create_icon('red')
                self.icon.title = "Robot Runner (Stopped)"

            # Actualizar el menú para refrescar el estado de los elementos
            try:
                self.icon.update_menu()
            except AttributeError:
                # Si update_menu() no existe, intentar recrear el menú
                self.icon.menu = self.create_menu()

    def get_status_text(self):
        """Obtiene el texto del estado actual."""
        # Verificar procesos en nuestro puerto específico
        try:
            result = subprocess.run(
                ['lsof', '-t', '-i', f':{self.port}', '-sTCP:LISTEN'],
                capture_output=True,
                text=True,
                timeout=5
            )
            pids = [int(pid) for pid in result.stdout.strip().split('\n') if pid]
            if pids:
                return f"✅ Running (PIDs: {', '.join(map(str, pids))})"
            else:
                return "⛔ Stopped"
        except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
            return "⛔ Stopped"

    def start_server(self):
        """Inicia el servidor Robot Runner."""
        if self.is_running:
            print("⚠️  El servidor ya está corriendo")
            return

        print("🚀 Iniciando servidor...")

        # Cambiar icono a amarillo (iniciando)
        if self.icon:
            self.icon.icon = self.create_icon('yellow')
            self.icon.title = "Robot Runner (Starting...)"

        # Iniciar servidor como subprocess
        try:
            # Usar ruta absoluta al archivo run.py
            run_py = os.path.join(PROJECT_ROOT, 'run.py')

            # Nota: stdout y stderr van a la terminal para ver los prints
            # Los logs de la aplicación se guardan en ~/Robot/requests.log
            self.server_process = subprocess.Popen(
                [sys.executable, run_py, '--server-only'],
                cwd=PROJECT_ROOT,
                stdout=None,  # Heredar stdout de la terminal
                stderr=None,  # Heredar stderr de la terminal
                start_new_session=True
            )

            # Esperar un poco para que inicie
            print("⏳ Esperando a que el servidor inicie...")
            time.sleep(5)

            # Verificar que inició correctamente en NUESTRO puerto
            try:
                result = subprocess.run(
                    ['lsof', '-t', '-i', f':{self.port}', '-sTCP:LISTEN'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                pids = [int(pid) for pid in result.stdout.strip().split('\n') if pid]

                if pids:
                    self.is_running = True
                    print(f"✅ Servidor iniciado correctamente en puerto {self.port} (PIDs: {', '.join(map(str, pids))})")
                else:
                    print(f"❌ Error: No se detectó servidor en puerto {self.port}")
                    print(f"   Revisa los logs de la terminal o en ~/Robot/requests.log")
            except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
                print("❌ Error al verificar el estado del servidor")
                self.is_running = False

        except Exception as e:
            print(f"❌ Error al iniciar servidor: {e}")
            import traceback
            traceback.print_exc()

        self.update_icon()

    def stop_server(self):
        """Detiene el servidor Robot Runner."""
        if not self.is_running:
            print("⚠️  El servidor no está corriendo")
            return

        print(f"⛔ Deteniendo servidor en puerto {self.port}...")

        # Buscar procesos en NUESTRO puerto específico
        try:
            result = subprocess.run(
                ['lsof', '-t', '-i', f':{self.port}', '-sTCP:LISTEN'],
                capture_output=True,
                text=True,
                timeout=5
            )
            pids = [int(pid) for pid in result.stdout.strip().split('\n') if pid]

            if not pids:
                print(f"⚠️  No se encontraron procesos en puerto {self.port}")
                self.is_running = False
                self.update_icon()
                return

            # Intentar terminación grácil (SIGTERM)
            print(f"   Encontrados {len(pids)} proceso(s): {', '.join(map(str, pids))}")
            for pid in pids:
                print(f"   Deteniendo PID {pid}...")
                kill_process(pid, force=False)

            # Esperar un poco
            time.sleep(2)

            # Verificar si quedan procesos en nuestro puerto
            result = subprocess.run(
                ['lsof', '-t', '-i', f':{self.port}', '-sTCP:LISTEN'],
                capture_output=True,
                text=True,
                timeout=5
            )
            remaining = [int(pid) for pid in result.stdout.strip().split('\n') if pid]

            if remaining:
                print(f"   Forzando terminación de {len(remaining)} proceso(s)...")
                for pid in remaining:
                    print(f"   Forzando PID {pid}...")
                    kill_process(pid, force=True)
                time.sleep(1)

            print(f"✅ Servidor detenido (puerto {self.port})")

        except (subprocess.TimeoutExpired, FileNotFoundError, ValueError) as e:
            print(f"⚠️  Error al detener servidor: {e}")

        # Actualizar estado
        self.is_running = False
        self.update_icon()

    def restart_server(self):
        """Reinicia el servidor."""
        print("🔄 Reiniciando servidor...")
        self.stop_server()
        time.sleep(2)
        self.start_server()

    def open_web_interface(self):
        """Abre la interfaz web en el navegador."""
        print(f"🌐 Abriendo interfaz web: {self.server_url}")
        webbrowser.open(self.server_url)

    def open_logs(self):
        """Abre el archivo de logs."""
        log_file = Path.home() / 'Robot' / 'requests.log'

        if log_file.exists():
            # Intentar abrir con el editor por defecto
            if sys.platform == 'darwin':  # macOS
                subprocess.Popen(['open', str(log_file)])
            elif sys.platform == 'win32':  # Windows
                os.startfile(str(log_file))
            else:  # Linux
                subprocess.Popen(['xdg-open', str(log_file)])
            print(f"📋 Abriendo logs: {log_file}")
        else:
            print(f"⚠️  Archivo de logs no encontrado: {log_file}")

    def show_status(self):
        """Muestra el estado del servidor en consola."""
        status = self.get_status_text()
        print(f"\n{'='*60}")
        print(f"Estado del Servidor: {status}")
        print(f"Puerto: {self.port}")
        print(f"URL: {self.server_url}")
        print(f"{'='*60}\n")

    def create_menu(self):
        """Crea el menú del tray."""
        return pystray.Menu(
            item(
                'Estado',
                lambda: self.show_status(),
                default=True
            ),
            pystray.Menu.SEPARATOR,
            item(
                'Iniciar Servidor',
                lambda: threading.Thread(target=self.start_server, daemon=True).start(),
                enabled=lambda item: not self.is_running
            ),
            item(
                'Detener Servidor',
                lambda: threading.Thread(target=self.stop_server, daemon=True).start(),
                enabled=lambda item: self.is_running
            ),
            item(
                'Reiniciar Servidor',
                lambda: threading.Thread(target=self.restart_server, daemon=True).start(),
                enabled=lambda item: self.is_running
            ),
            pystray.Menu.SEPARATOR,
            item(
                'Abrir Interfaz Web',
                lambda: self.open_web_interface(),
                enabled=lambda item: self.is_running
            ),
            item(
                'Ver Logs',
                lambda: self.open_logs()
            ),
            pystray.Menu.SEPARATOR,
            item(
                'Salir',
                lambda: self.quit_app()
            )
        )

    def quit_app(self):
        """Sale de la aplicación."""
        print("\n👋 Cerrando aplicación...")

        # Preguntar si detener el servidor
        if self.is_running:
            print("⚠️  El servidor está corriendo.")
            print("   El servidor continuará ejecutándose en background.")
            print("   Para detenerlo, usa 'Detener Servidor' antes de salir.")

        # Detener el icono
        if self.icon:
            self.icon.stop()

    def run(self):
        """Ejecuta la aplicación del tray."""
        print("=" * 60)
        print("  Robot Runner - System Tray App")
        print("=" * 60)
        print()
        print(f"📡 Puerto: {self.port}")
        print(f"🌐 URL: {self.server_url}")
        print()
        print(f"Estado inicial: {self.get_status_text()}")
        print()
        print("✨ Aplicación iniciada. Busca el icono en la bandeja del sistema.")
        print("   Haz clic derecho en el icono para ver las opciones.")
        print()
        print("Para salir: Haz clic en 'Salir' en el menú del tray")
        print("=" * 60)
        print()

        # Crear y ejecutar el icono del tray
        self.icon = pystray.Icon(
            "robot_runner",
            self.create_icon('green' if self.is_running else 'red'),
            "Robot Runner" + (" (Running)" if self.is_running else " (Stopped)"),
            self.create_menu()
        )

        # Actualizar estado periódicamente
        def update_status():
            while True:
                time.sleep(5)  # Verificar cada 5 segundos
                old_status = self.is_running
                self.check_initial_status()

                # Si cambió el estado, actualizar icono
                if old_status != self.is_running:
                    self.update_icon()

        # Iniciar thread de actualización
        threading.Thread(target=update_status, daemon=True).start()

        # Ejecutar el tray (bloqueante)
        self.icon.run()


def main():
    """Función principal."""
    try:
        app = RobotRunnerTray()
        app.run()
    except KeyboardInterrupt:
        print("\n\n👋 Aplicación cerrada por el usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()