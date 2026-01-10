#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Configura Cloudflare Tunnel en Windows para Robot Runner

.DESCRIPTION
    Script automatizado que:
    - Verifica instalación de cloudflared
    - Detecta credenciales del tunnel
    - Crea archivo de configuración
    - Instala como servicio de Windows
    - Inicia el tunnel

.EXAMPLE
    .\setup_tunnel_windows.ps1
#>

$ErrorActionPreference = "Stop"

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  🌐 CONFIGURACIÓN CLOUDFLARE TUNNEL - WINDOWS" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar cloudflared instalado
Write-Host "1. Verificando cloudflared..." -ForegroundColor Yellow
try {
    $version = cloudflared --version
    Write-Host "   ✅ cloudflared instalado: $version" -ForegroundColor Green
} catch {
    Write-Host "   ❌ cloudflared no está instalado" -ForegroundColor Red
    Write-Host "   Instalar con: choco install cloudflared" -ForegroundColor Red
    Write-Host "   O descargar desde: https://github.com/cloudflare/cloudflared/releases" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 2. Detectar directorio de cloudflared
$CloudflaredDir = Join-Path $env:USERPROFILE ".cloudflared"
Write-Host "2. Buscando configuración de Cloudflare..." -ForegroundColor Yellow
Write-Host "   Directorio: $CloudflaredDir" -ForegroundColor Gray

if (-not (Test-Path $CloudflaredDir)) {
    Write-Host "   ❌ No se encontró directorio .cloudflared" -ForegroundColor Red
    Write-Host "   Ejecutar primero: cloudflared tunnel login" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 3. Buscar archivos de credenciales (*.json)
Write-Host "3. Detectando tunnel..." -ForegroundColor Yellow
$CredFiles = Get-ChildItem -Path $CloudflaredDir -Filter "*.json" -ErrorAction SilentlyContinue

if ($CredFiles.Count -eq 0) {
    Write-Host "   ❌ No se encontraron credenciales de tunnel" -ForegroundColor Red
    Write-Host "   Crear un tunnel con: cloudflared tunnel create <nombre>" -ForegroundColor Red
    exit 1
}

if ($CredFiles.Count -gt 1) {
    Write-Host "   ⚠️  Se encontraron múltiples tunnels:" -ForegroundColor Yellow
    for ($i = 0; $i -lt $CredFiles.Count; $i++) {
        Write-Host "   [$i] $($CredFiles[$i].BaseName)" -ForegroundColor Gray
    }
    $selection = Read-Host "   Selecciona el número del tunnel a usar"
    $CredFile = $CredFiles[$selection]
} else {
    $CredFile = $CredFiles[0]
}

$TunnelID = $CredFile.BaseName
$CredFilePath = $CredFile.FullName

Write-Host "   ✅ Tunnel ID: $TunnelID" -ForegroundColor Green
Write-Host "   ✅ Credenciales: $CredFilePath" -ForegroundColor Green
Write-Host ""

# 4. Obtener información del tunnel
Write-Host "4. Obteniendo información del tunnel..." -ForegroundColor Yellow
try {
    $tunnelInfo = cloudflared tunnel info $TunnelID 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Tunnel encontrado" -ForegroundColor Green
    }
} catch {
    Write-Host "   ⚠️  No se pudo obtener info del tunnel (puede ser normal)" -ForegroundColor Yellow
}
Write-Host ""

# 5. Solicitar configuración
Write-Host "5. Configuración..." -ForegroundColor Yellow
Write-Host ""

# Hostname
Write-Host "   Ingresa el hostname (subdominio) del tunnel:" -ForegroundColor Cyan
Write-Host "   Ejemplo: robot.tudominio.com" -ForegroundColor Gray
$Hostname = Read-Host "   Hostname"

if ([string]::IsNullOrWhiteSpace($Hostname)) {
    Write-Host "   ❌ Hostname es requerido" -ForegroundColor Red
    exit 1
}

# Puerto local
Write-Host ""
Write-Host "   Ingresa el puerto de Robot Runner (default: 8088):" -ForegroundColor Cyan
$PortInput = Read-Host "   Puerto [8088]"
$Port = if ([string]::IsNullOrWhiteSpace($PortInput)) { "8088" } else { $PortInput }

Write-Host ""
Write-Host "   ✅ Hostname: $Hostname" -ForegroundColor Green
Write-Host "   ✅ Puerto: $Port" -ForegroundColor Green
Write-Host ""

# 6. Crear archivo config.yml
Write-Host "6. Creando archivo de configuración..." -ForegroundColor Yellow
$ConfigPath = Join-Path $CloudflaredDir "config.yml"

# Backup del config anterior si existe
if (Test-Path $ConfigPath) {
    $BackupPath = "$ConfigPath.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Copy-Item $ConfigPath $BackupPath
    Write-Host "   📦 Backup creado: $BackupPath" -ForegroundColor Gray
}

# Crear config
$ConfigContent = @"
tunnel: $TunnelID
credentials-file: $CredFilePath

ingress:
  - hostname: $Hostname
    service: http://localhost:$Port
  - service: http_status:404
"@

Set-Content -Path $ConfigPath -Value $ConfigContent -Encoding UTF8
Write-Host "   ✅ Configuración creada: $ConfigPath" -ForegroundColor Green
Write-Host ""

# 7. Mostrar contenido
Write-Host "7. Contenido del archivo de configuración:" -ForegroundColor Yellow
Write-Host "   ─────────────────────────────────────────" -ForegroundColor Gray
Write-Host $ConfigContent -ForegroundColor Gray
Write-Host "   ─────────────────────────────────────────" -ForegroundColor Gray
Write-Host ""

# 8. Preguntar si instalar como servicio
Write-Host "8. Instalación como servicio de Windows..." -ForegroundColor Yellow
$InstallService = Read-Host "   ¿Instalar como servicio? (s/n) [s]"

if ([string]::IsNullOrWhiteSpace($InstallService) -or $InstallService -eq "s" -or $InstallService -eq "S") {
    Write-Host ""
    Write-Host "   ⚠️  Se requieren permisos de Administrador" -ForegroundColor Yellow
    Write-Host "   Instalando servicio..." -ForegroundColor Yellow

    try {
        # Verificar si el servicio ya existe
        $existingService = Get-Service -Name "cloudflared" -ErrorAction SilentlyContinue

        if ($existingService) {
            Write-Host "   ⚠️  Servicio ya existe, reinstalando..." -ForegroundColor Yellow
            cloudflared service uninstall
            Start-Sleep -Seconds 2
        }

        cloudflared service install

        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ Servicio instalado correctamente" -ForegroundColor Green
            Write-Host ""

            # Iniciar servicio
            Write-Host "   Iniciando servicio..." -ForegroundColor Yellow
            Start-Service cloudflared
            Start-Sleep -Seconds 3

            # Verificar estado
            $service = Get-Service cloudflared
            if ($service.Status -eq "Running") {
                Write-Host "   ✅ Servicio iniciado correctamente" -ForegroundColor Green
            } else {
                Write-Host "   ⚠️  Servicio instalado pero no está corriendo" -ForegroundColor Yellow
                Write-Host "   Estado: $($service.Status)" -ForegroundColor Gray
                Write-Host "   Iniciar con: sc start cloudflared" -ForegroundColor Gray
            }
        } else {
            Write-Host "   ❌ Error al instalar servicio" -ForegroundColor Red
            Write-Host "   Ejecuta este script como Administrador" -ForegroundColor Red
        }
    } catch {
        Write-Host "   ❌ Error: $_" -ForegroundColor Red
        Write-Host "   Ejecuta este script como Administrador" -ForegroundColor Red
    }
} else {
    Write-Host "   ⏭️  Instalación de servicio omitida" -ForegroundColor Gray
    Write-Host "   Para iniciar manualmente: cloudflared tunnel run" -ForegroundColor Gray
}

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  ✅ CONFIGURACIÓN COMPLETADA" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Resumen:" -ForegroundColor Cyan
Write-Host "   • Tunnel ID: $TunnelID" -ForegroundColor White
Write-Host "   • Hostname: $Hostname" -ForegroundColor White
Write-Host "   • Puerto local: $Port" -ForegroundColor White
Write-Host "   • Config: $ConfigPath" -ForegroundColor White
Write-Host ""
Write-Host "🌐 Acceso:" -ForegroundColor Cyan
Write-Host "   https://$Hostname" -ForegroundColor White
Write-Host ""
Write-Host "🔧 Comandos útiles:" -ForegroundColor Cyan
Write-Host "   • Ver estado: sc query cloudflared" -ForegroundColor Gray
Write-Host "   • Iniciar: sc start cloudflared" -ForegroundColor Gray
Write-Host "   • Detener: sc stop cloudflared" -ForegroundColor Gray
Write-Host "   • Logs: Get-EventLog -LogName Application -Source cloudflared -Newest 20" -ForegroundColor Gray
Write-Host ""
Write-Host "✨ El tunnel está configurado y listo!" -ForegroundColor Green
Write-Host ""