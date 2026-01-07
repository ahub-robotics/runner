"""
Robot Runner - Sistema de Ejecución Remota de Robots

Este paquete contiene todos los módulos del servidor Robot Runner.

Módulos:
    - app: Aplicación Flask + Gunicorn (entry point del servidor)
    - server: Wrapper del Runner con métodos de alto nivel
    - robot: Lógica de ejecución de robots y control de procesos
    - config: Gestión de configuración

Compatible con Windows, Linux y macOS.
"""

__version__ = "1.0.0"
__author__ = "Robot Runner Team"

# Exportar clases principales para facilitar imports
from .server import Server
from .robot import Robot, Runner

__all__ = ['Server', 'Robot', 'Runner']