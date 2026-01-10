#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Configura el entorno Python para Robot Runner

.DESCRIPTION
    - Crea virtualenv
    - Instala dependencias de requirements.txt
    - Verifica instalación de Celery y otras dependencias críticas

.EXAMPLE
    .\setup_python_env.ps1
#>

$ErrorActionPreference = "Stop"

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  🐍 CONFIGURACIÓN DEL ENTORNO PYTHON - ROBOT RUNNER" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# Obtener directorio del proyecto (2 niveles arriba)
$ScriptDir = Split-Path -Parent $PSCommandPath
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)

Write-Host "📁 Directorio del proyecto: $ProjectRoot" -ForegroundColor Gray
Write-Host ""

# Verificar que Python está instalado
Write-Host "1. Verificando Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "   ✅ Python instalado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Python no está instalado" -ForegroundColor Red
    Write-Host "   Ejecuta primero: .\install_dependencies.ps1" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# Verificar requirements.txt
Write-Host "2. Verificando requirements.txt..." -ForegroundColor Yellow
$RequirementsFile = Join-Path $ProjectRoot "requirements.txt"
if (-not (Test-Path $RequirementsFile)) {
    Write-Host "   ❌ No se encontró requirements.txt en: $RequirementsFile" -ForegroundColor Red
    exit 1
}
Write-Host "   ✅ requirements.txt encontrado" -ForegroundColor Green
Write-Host ""

# Crear virtualenv
Write-Host "3. Creando virtualenv..." -ForegroundColor Yellow
$VenvPath = Join-Path $ProjectRoot "venv"

if (Test-Path $VenvPath) {
    Write-Host "   ⚠️  Virtualenv ya existe en: $VenvPath" -ForegroundColor Yellow
    $response = Read-Host "   ¿Quieres recrearlo? (s/n) [n]"
    if ($response -eq "s" -or $response -eq "S") {
        Write-Host "   🗑️  Eliminando virtualenv anterior..." -ForegroundColor Gray
        Remove-Item -Recurse -Force $VenvPath
    } else {
        Write-Host "   ⏭️  Usando virtualenv existente" -ForegroundColor Gray
        Write-Host ""
        # Continuar con la instalación de dependencias
        goto InstallDeps
    }
}

Write-Host "   📦 Creando virtualenv en: $VenvPath" -ForegroundColor Gray
python -m venv $VenvPath

if ($LASTEXITCODE -ne 0) {
    Write-Host "   ❌ Error al crear virtualenv" -ForegroundColor Red
    exit 1
}

Write-Host "   ✅ Virtualenv creado correctamente" -ForegroundColor Green
Write-Host ""

:InstallDeps
# Activar virtualenv e instalar dependencias
Write-Host "4. Instalando dependencias..." -ForegroundColor Yellow

$ActivateScript = Join-Path $VenvPath "Scripts\Activate.ps1"
if (-not (Test-Path $ActivateScript)) {
    Write-Host "   ❌ No se encontró script de activación: $ActivateScript" -ForegroundColor Red
    exit 1
}

# Cambiar al directorio del proyecto
Push-Location $ProjectRoot

try {
    # Activar virtualenv
    Write-Host "   🔄 Activando virtualenv..." -ForegroundColor Gray
    & $ActivateScript

    # Actualizar pip
    Write-Host "   📦 Actualizando pip..." -ForegroundColor Gray
    python -m pip install --upgrade pip | Out-Null

    # Instalar dependencias
    Write-Host "   📦 Instalando dependencias desde requirements.txt..." -ForegroundColor Gray
    Write-Host "      (esto puede tardar varios minutos)" -ForegroundColor Gray
    pip install -r requirements.txt

    if ($LASTEXITCODE -ne 0) {
        Write-Host "   ❌ Error al instalar dependencias" -ForegroundColor Red
        exit 1
    }

    Write-Host "   ✅ Dependencias instaladas correctamente" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Error: $_" -ForegroundColor Red
    exit 1
} finally {
    Pop-Location
}
Write-Host ""

# Verificar instalación de paquetes críticos
Write-Host "5. Verificando paquetes críticos..." -ForegroundColor Yellow

$CriticalPackages = @("flask", "celery", "waitress", "pika", "pillow")
$AllInstalled = $true

foreach ($package in $CriticalPackages) {
    try {
        & "$VenvPath\Scripts\python.exe" -c "import $package" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ $package" -ForegroundColor Green
        } else {
            Write-Host "   ❌ $package - no instalado" -ForegroundColor Red
            $AllInstalled = $false
        }
    } catch {
        Write-Host "   ❌ $package - error al verificar" -ForegroundColor Red
        $AllInstalled = $false
    }
}
Write-Host ""

# Resumen
Write-Host "======================================================================" -ForegroundColor Cyan
if ($AllInstalled) {
    Write-Host "  ✅ ENTORNO PYTHON CONFIGURADO CORRECTAMENTE" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  ENTORNO PYTHON CONFIGURADO CON ADVERTENCIAS" -ForegroundColor Yellow
}
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Virtualenv:" -ForegroundColor Cyan
Write-Host "   Ruta: $VenvPath" -ForegroundColor White
Write-Host "   Activar: .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host ""
Write-Host "📝 Siguiente paso:" -ForegroundColor Cyan
Write-Host "   Ejecuta: .\setup_rabbitmq.ps1" -ForegroundColor White
Write-Host ""