#!/usr/bin/env python3
"""
================================================================================
Robot Runner - Main Entry Point
================================================================================

Punto de entrada principal de la aplicación Robot Runner.
Delega a los módulos especializados en cli/.

Uso:
    # Servidor (modo producción):
    python run.py

    # System tray (modo desarrollo/local):
    python run.py --tray

    # Modo legacy (src.app.main):
    python run.py --legacy

Nuevos entry points directos:
    python cli/run_server.py    # Solo servidor
    python cli/run_tray.py      # Solo system tray

Para más información, ver docs/TECHNICAL-DOCUMENTATION.md

================================================================================
"""
import sys


def main():
    """
    Punto de entrada principal.

    Delega a los módulos especializados según los argumentos.
    """
    # Verificar argumentos
    if '--tray' in sys.argv:
        # Remover --tray de sys.argv para no confundir al módulo
        sys.argv.remove('--tray')
        # Ejecutar system tray
        from cli.run_tray import main as tray_main
        tray_main()
    elif '--legacy' in sys.argv:
        # Remover --legacy de sys.argv
        sys.argv.remove('--legacy')
        # Ejecutar versión legacy (src.app.main)
        from src.app import main as legacy_main
        legacy_main()
    else:
        # Por defecto: ejecutar servidor
        from cli.run_server import main as server_main
        server_main()


if __name__ == '__main__':
    main()