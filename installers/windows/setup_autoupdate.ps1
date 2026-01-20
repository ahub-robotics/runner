#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Configura el servicio de auto-actualización para Robot Runner en Windows

.DESCRIPTION
    Instala una tarea programada de Windows que ejecuta el update_service.py
    cada hora para verificar y aplicar actualizaciones automáticamente.

.PARAMETER Interval
    Intervalo entre verificaciones en segundos (por defecto: 3600 = 1 hora)

.PARAMETER Channel
    Canal de actualización: stable, beta, o canary (por defecto: stable)

.PARAMETER Repo
    Repositorio de GitHub en formato owner/repo

.EXAMPLE
    .\setup_autoupdate.ps1
    # Instala con configuración por defecto (cada 1 hora, canal stable)

.EXAMPLE
    .\setup_autoupdate.ps1 -Interval 1800 -Channel beta
    # Instala verificando cada 30 minutos en canal beta
#>

param(
    [int]$Interval = 3600,
    [ValidateSet('stable', 'beta', 'canary')]
    [string]$Channel = 'stable',
    [string]$Repo = 'tu-usuario/robotrunner_windows'
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  🔄 CONFIGURACIÓN DE AUTO-ACTUALIZACIÓN" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Verificar permisos de administrador
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "❌ Este script requiere permisos de Administrador" -ForegroundColor Red
    exit 1
}

# Obtener rutas
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$UpdateServiceScript = Join-Path $ProjectRoot "update_service.py"
$PythonExe = Get-Command python -ErrorAction SilentlyContinue

if (-not $PythonExe) {
    Write-Host "❌ Python no encontrado en PATH" -ForegroundColor Red
    Write-Host "   Instala Python 3.11 y vuelve a intentar" -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path $UpdateServiceScript)) {
    Write-Host "❌ No se encontró update_service.py en: $UpdateServiceScript" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Python encontrado: $($PythonExe.Source)" -ForegroundColor Green
Write-Host "✅ Update service: $UpdateServiceScript" -ForegroundColor Green
Write-Host ""

# Configuración
Write-Host "📋 Configuración:" -ForegroundColor Cyan
Write-Host "   Intervalo: $Interval segundos ($([math]::Round($Interval / 60)) minutos)" -ForegroundColor Gray
Write-Host "   Canal: $Channel" -ForegroundColor Gray
Write-Host "   Repositorio: $Repo" -ForegroundColor Gray
Write-Host ""

# Confirmar
$response = Read-Host "¿Deseas continuar? (s/n) [s]"
if ($response -eq "n" -or $response -eq "N") {
    Write-Host "Configuración cancelada" -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "⚙️  Creando tarea programada..." -ForegroundColor Yellow

try {
    # Nombre de la tarea
    $TaskName = "RobotRunner-AutoUpdate"

    # Eliminar tarea existente si existe
    $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existingTask) {
        Write-Host "   Eliminando tarea existente..." -ForegroundColor Gray
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }

    # Crear acción (comando a ejecutar)
    $Action = New-ScheduledTaskAction `
        -Execute $PythonExe.Source `
        -Argument "`"$UpdateServiceScript`" --interval $Interval --channel $Channel --repo $Repo" `
        -WorkingDirectory $ProjectRoot

    # Crear trigger (ejecutar al inicio y cada X minutos)
    $IntervalMinutes = [math]::Max(1, [math]::Round($Interval / 60))

    $Trigger1 = New-ScheduledTaskTrigger -AtStartup
    $Trigger2 = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes)

    # Configuración de la tarea
    $Settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RestartCount 3 `
        -RestartInterval (New-TimeSpan -Minutes 1)

    # Ejecutar como SYSTEM para que funcione sin usuario logueado
    $Principal = New-ScheduledTaskPrincipal `
        -UserId "SYSTEM" `
        -LogonType ServiceAccount `
        -RunLevel Highest

    # Registrar tarea
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $Action `
        -Trigger $Trigger1, $Trigger2 `
        -Settings $Settings `
        -Principal $Principal `
        -Description "Verifica y aplica actualizaciones automáticas para Robot Runner"

    Write-Host ""
    Write-Host "✅ Tarea programada creada exitosamente" -ForegroundColor Green
    Write-Host ""

    # Iniciar tarea inmediatamente para verificar
    Write-Host "🔍 Verificando actualizaciones disponibles..." -ForegroundColor Yellow
    Start-ScheduledTask -TaskName $TaskName
    Start-Sleep -Seconds 2

    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "  ✅ CONFIGURACIÓN COMPLETADA" -ForegroundColor Green
    Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📋 El servicio de auto-actualización está activo:" -ForegroundColor Cyan
    Write-Host "   • Verifica actualizaciones cada $IntervalMinutes minutos" -ForegroundColor Gray
    Write-Host "   • Se ejecuta automáticamente al iniciar Windows" -ForegroundColor Gray
    Write-Host "   • Actualiza el ejecutable cuando hay nueva versión" -ForegroundColor Gray
    Write-Host ""
    Write-Host "🔧 Para gestionar la tarea:" -ForegroundColor Cyan
    Write-Host "   • Ver estado:" -ForegroundColor White
    Write-Host "     Get-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   • Detener tarea:" -ForegroundColor White
    Write-Host "     Stop-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   • Desactivar auto-actualización:" -ForegroundColor White
    Write-Host "     Disable-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   • Eliminar tarea:" -ForegroundColor White
    Write-Host "     Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false" -ForegroundColor Gray
    Write-Host ""
    Write-Host "📝 Logs en: $env:USERPROFILE\Robot\logs\updater.log" -ForegroundColor Cyan
    Write-Host ""

} catch {
    Write-Host ""
    Write-Host "❌ Error al crear tarea programada: $_" -ForegroundColor Red
    Write-Host ""
    exit 1
}

Read-Host "Presiona Enter para finalizar"