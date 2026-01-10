#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Instala todas las dependencias del sistema para Robot Runner en Windows

.DESCRIPTION
    Instala automáticamente:
    - Chocolatey (gestor de paquetes)
    - Python 3.11
    - Git
    - Cloudflared
    - RabbitMQ Server
    - Erlang (requerido por RabbitMQ)

.EXAMPLE
    .\install_dependencies.ps1
#>

$ErrorActionPreference = "Stop"

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  📦 INSTALACIÓN DE DEPENDENCIAS - ROBOT RUNNER WINDOWS" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar permisos de administrador
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "❌ Este script requiere permisos de Administrador" -ForegroundColor Red
    Write-Host "   Ejecuta PowerShell como Administrador y vuelve a intentarlo" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Ejecutando con permisos de Administrador" -ForegroundColor Green
Write-Host ""

# 1. Instalar Chocolatey
Write-Host "1. Instalando Chocolatey..." -ForegroundColor Yellow
try {
    $chocoInstalled = Get-Command choco -ErrorAction SilentlyContinue
    if ($chocoInstalled) {
        Write-Host "   ✅ Chocolatey ya está instalado" -ForegroundColor Green
    } else {
        Write-Host "   📥 Descargando e instalando Chocolatey..." -ForegroundColor Gray
        Set-ExecutionPolicy Bypass -Scope Process -Force
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
        iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

        # Refrescar PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

        Write-Host "   ✅ Chocolatey instalado correctamente" -ForegroundColor Green
    }
} catch {
    Write-Host "   ❌ Error al instalar Chocolatey: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 2. Instalar Python 3.11
Write-Host "2. Instalando Python 3.11..." -ForegroundColor Yellow
try {
    $pythonInstalled = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonInstalled) {
        $pythonVersion = python --version 2>&1
        Write-Host "   ✅ Python ya está instalado: $pythonVersion" -ForegroundColor Green
    } else {
        Write-Host "   📥 Instalando Python 3.11..." -ForegroundColor Gray
        choco install python311 -y

        # Refrescar PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

        $pythonVersion = python --version 2>&1
        Write-Host "   ✅ Python instalado: $pythonVersion" -ForegroundColor Green
    }
} catch {
    Write-Host "   ❌ Error al instalar Python: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 3. Instalar Git
Write-Host "3. Instalando Git..." -ForegroundColor Yellow
try {
    $gitInstalled = Get-Command git -ErrorAction SilentlyContinue
    if ($gitInstalled) {
        $gitVersion = git --version
        Write-Host "   ✅ Git ya está instalado: $gitVersion" -ForegroundColor Green
    } else {
        Write-Host "   📥 Instalando Git..." -ForegroundColor Gray
        choco install git -y

        # Refrescar PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

        $gitVersion = git --version
        Write-Host "   ✅ Git instalado: $gitVersion" -ForegroundColor Green
    }
} catch {
    Write-Host "   ❌ Error al instalar Git: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 4. Instalar Cloudflared
Write-Host "4. Instalando Cloudflared..." -ForegroundColor Yellow
try {
    $cloudflaredInstalled = Get-Command cloudflared -ErrorAction SilentlyContinue
    if ($cloudflaredInstalled) {
        $cloudflaredVersion = cloudflared --version
        Write-Host "   ✅ Cloudflared ya está instalado: $cloudflaredVersion" -ForegroundColor Green
    } else {
        Write-Host "   📥 Instalando Cloudflared..." -ForegroundColor Gray
        choco install cloudflared -y

        # Refrescar PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

        $cloudflaredVersion = cloudflared --version
        Write-Host "   ✅ Cloudflared instalado: $cloudflaredVersion" -ForegroundColor Green
    }
} catch {
    Write-Host "   ❌ Error al instalar Cloudflared: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 5. Instalar Erlang (requerido por RabbitMQ)
Write-Host "5. Instalando Erlang..." -ForegroundColor Yellow
try {
    $erlangInstalled = Get-Command erl -ErrorAction SilentlyContinue
    if ($erlangInstalled) {
        Write-Host "   ✅ Erlang ya está instalado" -ForegroundColor Green
    } else {
        Write-Host "   📥 Instalando Erlang..." -ForegroundColor Gray
        choco install erlang -y

        # Refrescar PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

        Write-Host "   ✅ Erlang instalado correctamente" -ForegroundColor Green
    }
} catch {
    Write-Host "   ❌ Error al instalar Erlang: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 6. Instalar RabbitMQ
Write-Host "6. Instalando RabbitMQ Server..." -ForegroundColor Yellow
try {
    $rabbitmqService = Get-Service -Name RabbitMQ -ErrorAction SilentlyContinue
    if ($rabbitmqService) {
        Write-Host "   ✅ RabbitMQ ya está instalado" -ForegroundColor Green
        Write-Host "   Estado del servicio: $($rabbitmqService.Status)" -ForegroundColor Gray
    } else {
        Write-Host "   📥 Instalando RabbitMQ Server..." -ForegroundColor Gray
        choco install rabbitmq -y

        # Refrescar PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

        Write-Host "   ✅ RabbitMQ instalado correctamente" -ForegroundColor Green

        # Iniciar servicio
        Write-Host "   🔄 Iniciando servicio RabbitMQ..." -ForegroundColor Gray
        Start-Service RabbitMQ
        Start-Sleep -Seconds 5

        $rabbitmqService = Get-Service -Name RabbitMQ
        Write-Host "   ✅ Servicio RabbitMQ: $($rabbitmqService.Status)" -ForegroundColor Green
    }
} catch {
    Write-Host "   ❌ Error al instalar RabbitMQ: $_" -ForegroundColor Red
    Write-Host "   ⚠️  Puedes continuar, pero necesitarás configurar RabbitMQ manualmente" -ForegroundColor Yellow
}
Write-Host ""

# Resumen
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  ✅ INSTALACIÓN DE DEPENDENCIAS COMPLETADA" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Componentes instalados:" -ForegroundColor Cyan
Write-Host "   ✅ Chocolatey" -ForegroundColor Green
Write-Host "   ✅ Python 3.11" -ForegroundColor Green
Write-Host "   ✅ Git" -ForegroundColor Green
Write-Host "   ✅ Cloudflared" -ForegroundColor Green
Write-Host "   ✅ Erlang" -ForegroundColor Green
Write-Host "   ✅ RabbitMQ Server" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Siguiente paso:" -ForegroundColor Cyan
Write-Host "   Ejecuta: .\setup_python_env.ps1" -ForegroundColor White
Write-Host ""