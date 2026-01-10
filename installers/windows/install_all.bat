@echo off
REM =====================================================================
REM  Robot Runner - Instalador Windows
REM
REM  Este script ejecuta la instalación completa de Robot Runner
REM  IMPORTANTE: Ejecutar como Administrador
REM =====================================================================

echo.
echo ======================================================================
echo   ROBOT RUNNER - INSTALADOR WINDOWS
echo ======================================================================
echo.
echo Este script debe ejecutarse como Administrador
echo.

REM Verificar permisos de administrador
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo [ERROR] No tienes permisos de Administrador
    echo.
    echo Para ejecutar como Administrador:
    echo   1. Haz clic derecho en install_all.bat
    echo   2. Selecciona "Ejecutar como administrador"
    echo.
    pause
    exit /b 1
)

echo [OK] Ejecutando con permisos de Administrador
echo.

REM Ejecutar el script PowerShell
echo Iniciando instalacion...
echo.

powershell.exe -ExecutionPolicy Bypass -File "%~dp0install_all.ps1"

if %errorLevel% NEQ 0 (
    echo.
    echo [ERROR] La instalacion ha fallado
    echo.
    pause
    exit /b 1
)

echo.
echo [OK] Instalacion completada
echo.
pause