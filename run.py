#!/usr/bin/env python3
"""
================================================================================
Robot Runner - Entry Point
================================================================================

Este es el punto de entrada principal de la aplicación Robot Runner.
Importa y ejecuta la función main() del módulo src.app.

Uso:
    # Modo normal (GUI + Servidor):
    python run.py

    # Modo solo servidor (sin GUI):
    python run.py --server-only

    # Con configuración:
    python run.py --machine_id=ABC123 --license_key=XYZ789

Para más información, ver docs/FUNCTIONAL-DOCUMENTATION.md

================================================================================
"""

if __name__ == '__main__':
    # Importar y ejecutar la aplicación
    from src.app import main
    main()