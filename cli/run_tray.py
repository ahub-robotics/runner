#!/usr/bin/env python3
"""
================================================================================
Robot Runner - System Tray Entry Point
================================================================================

Entry point para ejecutar la aplicación de system tray de Robot Runner.

Uso:
    python cli/run_tray.py
    python -m cli.run_tray

Características:
    - Icono en la bandeja del sistema
    - Control del servidor (start/stop)
    - Acceso rápido a la interfaz web
    - Ver logs en tiempo real
    - Indicador visual de estado

Requisitos:
    pip install pystray pillow

Para más información, ver docs/SYSTEM-TRAY-APP.md

================================================================================
"""
import sys
from pathlib import Path

# Asegurar que el directorio raíz está en el path
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))


def main():
    """
    Punto de entrada de la aplicación de system tray.

    Ejecuta la GUI de bandeja del sistema para gestionar el servidor.
    """
    try:
        # Verificar dependencias
        try:
            import pystray
            from PIL import Image
        except ImportError:
            print("❌ Error: Dependencias de GUI no instaladas")
            print("   Instalar con: pip install pystray pillow")
            sys.exit(1)

        # Importar y ejecutar la aplicación de tray
        from gui.tray_app import RobotRunnerTray

        print("🎨 Iniciando aplicación de system tray...")
        print("   Busca el icono en la bandeja del sistema")
        print("   Haz clic derecho para ver opciones")
        print("\n⚠️  Para salir, usa 'Salir' en el menú del tray")
        print("   (Ctrl+C no funciona con aplicaciones de tray)\n")

        # Crear y ejecutar aplicación
        tray = RobotRunnerTray()
        tray.run()

    except KeyboardInterrupt:
        print("\n⚠️  Señal de interrupción recibida")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error al ejecutar la aplicación de tray: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
