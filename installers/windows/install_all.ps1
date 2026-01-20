#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Script maestro de instalación para Robot Runner en Windows

.DESCRIPTION
    Ejecuta todos los scripts de instalación en orden:
    1. install_dependencies.ps1 - Instala herramientas del sistema
    2. setup_python_env.ps1 - Configura Python y virtualenv
    3. setup_rabbitmq.ps1 - Configura RabbitMQ
    4. Opcionalmente: setup_tunnel.py - Configura Cloudflare Tunnel

.EXAMPLE
    .\install_all.ps1
#>

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  🚀 INSTALACIÓN COMPLETA - ROBOT RUNNER WINDOWS" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Este script instalará y configurará:" -ForegroundColor White
Write-Host "  • Chocolatey (gestor de paquetes)" -ForegroundColor Gray
Write-Host "  • Python 3.11" -ForegroundColor Gray
Write-Host "  • Git" -ForegroundColor Gray
Write-Host "  • Cloudflared" -ForegroundColor Gray
Write-Host "  • RabbitMQ + Erlang" -ForegroundColor Gray
Write-Host "  • Entorno virtual Python" -ForegroundColor Gray
Write-Host "  • Dependencias de Robot Runner (Celery, Flask, etc.)" -ForegroundColor Gray
Write-Host ""

# Verificar permisos de administrador
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "❌ Este script requiere permisos de Administrador" -ForegroundColor Red
    Write-Host ""
    Write-Host "Para ejecutar como Administrador:" -ForegroundColor Yellow
    Write-Host "  1. Presiona Win + X" -ForegroundColor Gray
    Write-Host "  2. Selecciona 'Windows PowerShell (Administrador)'" -ForegroundColor Gray
    Write-Host "  3. Navega a esta carpeta y ejecuta el script de nuevo" -ForegroundColor Gray
    Write-Host ""
    Read-Host "Presiona Enter para salir"
    exit 1
}

Write-Host "✅ Ejecutando con permisos de Administrador" -ForegroundColor Green
Write-Host ""

$response = Read-Host "¿Deseas continuar con la instalación? (s/n) [s]"
if ($response -eq "n" -or $response -eq "N") {
    Write-Host "Instalación cancelada" -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# Obtener directorio del script
$ScriptDir = Split-Path -Parent $PSCommandPath

# Paso 1: Instalar dependencias del sistema
Write-Host "╔════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  PASO 1/3: INSTALACIÓN DE DEPENDENCIAS DEL SISTEMA                ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

try {
    & "$ScriptDir\install_dependencies.ps1"
    if ($LASTEXITCODE -ne 0) {
        throw "Error en install_dependencies.ps1"
    }
} catch {
    Write-Host ""
    Write-Host "❌ Error en la instalación de dependencias: $_" -ForegroundColor Red
    Write-Host ""
    Read-Host "Presiona Enter para salir"
    exit 1
}

Write-Host ""
Read-Host "Presiona Enter para continuar con el siguiente paso"
Write-Host ""

# Paso 2: Configurar entorno Python
Write-Host "╔════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  PASO 2/3: CONFIGURACIÓN DEL ENTORNO PYTHON                       ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

try {
    & "$ScriptDir\setup_python_env.ps1"
    if ($LASTEXITCODE -ne 0) {
        throw "Error en setup_python_env.ps1"
    }
} catch {
    Write-Host ""
    Write-Host "❌ Error en la configuración de Python: $_" -ForegroundColor Red
    Write-Host ""
    Read-Host "Presiona Enter para salir"
    exit 1
}

Write-Host ""
Read-Host "Presiona Enter para continuar con el siguiente paso"
Write-Host ""

# Paso 3: Configurar RabbitMQ
Write-Host "╔════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  PASO 3/3: CONFIGURACIÓN DE RABBITMQ                              ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

try {
    & "$ScriptDir\setup_rabbitmq.ps1"
    if ($LASTEXITCODE -ne 0) {
        throw "Error en setup_rabbitmq.ps1"
    }
} catch {
    Write-Host ""
    Write-Host "❌ Error en la configuración de RabbitMQ: $_" -ForegroundColor Red
    Write-Host ""
    Read-Host "Presiona Enter para salir"
    exit 1
}

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  ✅ INSTALACIÓN COMPLETADA CON ÉXITO" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# Paso opcional: Cloudflare Tunnel
Write-Host "📝 PASO OPCIONAL: Configurar Cloudflare Tunnel" -ForegroundColor Cyan
Write-Host ""
$setupTunnel = Read-Host "¿Quieres configurar Cloudflare Tunnel ahora? (s/n) [n]"

if ($setupTunnel -eq "s" -or $setupTunnel -eq "S") {
    Write-Host ""
    Write-Host "🌐 Configurando Cloudflare Tunnel..." -ForegroundColor Yellow
    Write-Host ""

    $ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)
    $TunnelScript = Join-Path $ProjectRoot "setup_tunnel.py"

    if (Test-Path $TunnelScript) {
        try {
            & python $TunnelScript
        } catch {
            Write-Host ""
            Write-Host "⚠️  Error al configurar tunnel: $_" -ForegroundColor Yellow
            Write-Host "   Puedes ejecutarlo manualmente más tarde:" -ForegroundColor Gray
            Write-Host "   python setup_tunnel.py" -ForegroundColor Gray
        }
    } else {
        Write-Host "⚠️  No se encontró setup_tunnel.py" -ForegroundColor Yellow
        Write-Host "   Busca el script en la raíz del proyecto" -ForegroundColor Gray
    }
} else {
    Write-Host ""
    Write-Host "⏭️  Configuración de tunnel omitida" -ForegroundColor Gray
    Write-Host "   Para configurarlo más tarde, ejecuta:" -ForegroundColor Gray
    Write-Host "   python setup_tunnel.py" -ForegroundColor Gray
}

# Paso opcional: Auto-Update Service
Write-Host ""
Write-Host "📝 PASO OPCIONAL: Configurar Auto-Actualización" -ForegroundColor Cyan
Write-Host ""
$setupAutoUpdate = Read-Host "¿Quieres configurar actualizaciones automáticas? (s/n) [n]"

if ($setupAutoUpdate -eq "s" -or $setupAutoUpdate -eq "S") {
    Write-Host ""
    Write-Host "🔄 Configurando Auto-Actualización..." -ForegroundColor Yellow
    Write-Host ""

    try {
        & "$ScriptDir\setup_autoupdate.ps1"
    } catch {
        Write-Host ""
        Write-Host "⚠️  Error al configurar auto-update: $_" -ForegroundColor Yellow
        Write-Host "   Puedes ejecutarlo manualmente más tarde:" -ForegroundColor Gray
        Write-Host "   .\installers\windows\setup_autoupdate.ps1" -ForegroundColor Gray
    }
} else {
    Write-Host ""
    Write-Host "⏭️  Configuración de auto-update omitida" -ForegroundColor Gray
    Write-Host "   Para configurarlo más tarde, ejecuta:" -ForegroundColor Gray
    Write-Host "   .\installers\windows\setup_autoupdate.ps1" -ForegroundColor Gray
}

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  🎉 ¡TODO LISTO!" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Resumen de instalación:" -ForegroundColor Cyan
Write-Host "   ✅ Dependencias del sistema instaladas" -ForegroundColor Green
Write-Host "   ✅ Entorno Python configurado" -ForegroundColor Green
Write-Host "   ✅ RabbitMQ configurado" -ForegroundColor Green
Write-Host ""
Write-Host "🚀 Para iniciar Robot Runner:" -ForegroundColor Cyan
Write-Host "   1. Activa el virtualenv:" -ForegroundColor White
Write-Host "      .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "   2. Configura tu config.json con machine_id y token" -ForegroundColor White
Write-Host ""
Write-Host "   3. Inicia el servidor:" -ForegroundColor White
Write-Host "      python main.py" -ForegroundColor Gray
Write-Host ""
Write-Host "📖 Documentación adicional en el README.md" -ForegroundColor Cyan
Write-Host ""
Read-Host "Presiona Enter para finalizar"