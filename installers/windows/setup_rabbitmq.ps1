#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Configura RabbitMQ para Robot Runner

.DESCRIPTION
    - Verifica que el servicio RabbitMQ está corriendo
    - Habilita plugin de management (interfaz web)
    - Configura usuario y permisos (opcional)
    - Verifica conectividad

.EXAMPLE
    .\setup_rabbitmq.ps1
#>

$ErrorActionPreference = "Stop"

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  🐰 CONFIGURACIÓN DE RABBITMQ - ROBOT RUNNER" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar permisos de administrador
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "❌ Este script requiere permisos de Administrador" -ForegroundColor Red
    exit 1
}

# 1. Verificar servicio RabbitMQ
Write-Host "1. Verificando servicio RabbitMQ..." -ForegroundColor Yellow
try {
    $rabbitmqService = Get-Service -Name RabbitMQ -ErrorAction Stop
    Write-Host "   ✅ Servicio encontrado: $($rabbitmqService.DisplayName)" -ForegroundColor Green
    Write-Host "   Estado: $($rabbitmqService.Status)" -ForegroundColor Gray

    if ($rabbitmqService.Status -ne "Running") {
        Write-Host "   🔄 Iniciando servicio..." -ForegroundColor Yellow
        Start-Service RabbitMQ
        Start-Sleep -Seconds 5
        $rabbitmqService = Get-Service -Name RabbitMQ
        Write-Host "   ✅ Servicio iniciado: $($rabbitmqService.Status)" -ForegroundColor Green
    }
} catch {
    Write-Host "   ❌ RabbitMQ no está instalado" -ForegroundColor Red
    Write-Host "   Ejecuta primero: .\install_dependencies.ps1" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# 2. Verificar rabbitmqctl
Write-Host "2. Verificando herramientas de RabbitMQ..." -ForegroundColor Yellow
try {
    $rabbitmqctl = Get-Command rabbitmqctl -ErrorAction SilentlyContinue
    if (-not $rabbitmqctl) {
        # Buscar en ubicaciones comunes
        $possiblePaths = @(
            "C:\Program Files\RabbitMQ Server\rabbitmq_server-*\sbin\rabbitmqctl.bat",
            "C:\Program Files (x86)\RabbitMQ Server\rabbitmq_server-*\sbin\rabbitmqctl.bat"
        )

        $rabbitmqctlPath = $null
        foreach ($pattern in $possiblePaths) {
            $found = Get-ChildItem -Path $pattern -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($found) {
                $rabbitmqctlPath = $found.FullName
                break
            }
        }

        if ($rabbitmqctlPath) {
            Write-Host "   ✅ rabbitmqctl encontrado en: $rabbitmqctlPath" -ForegroundColor Green
            # Agregar al PATH temporalmente
            $env:Path += ";$(Split-Path -Parent $rabbitmqctlPath)"
        } else {
            Write-Host "   ⚠️  No se encontró rabbitmqctl en el PATH" -ForegroundColor Yellow
            Write-Host "   Puedes continuar, pero algunas configuraciones pueden fallar" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   ✅ rabbitmqctl disponible" -ForegroundColor Green
    }
} catch {
    Write-Host "   ⚠️  Error al verificar rabbitmqctl: $_" -ForegroundColor Yellow
}
Write-Host ""

# 3. Habilitar plugin de management
Write-Host "3. Habilitando RabbitMQ Management Plugin..." -ForegroundColor Yellow
try {
    rabbitmqctl list_plugins | Out-Null
    rabbitmq-plugins enable rabbitmq_management 2>&1 | Out-Null

    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Plugin habilitado correctamente" -ForegroundColor Green
        Write-Host "   🌐 Interfaz web disponible en: http://localhost:15672" -ForegroundColor Gray
        Write-Host "   Usuario por defecto: guest / guest" -ForegroundColor Gray
    } else {
        Write-Host "   ⚠️  No se pudo habilitar el plugin" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ⚠️  Error al habilitar plugin: $_" -ForegroundColor Yellow
}
Write-Host ""

# 4. Verificar conectividad
Write-Host "4. Verificando conectividad con RabbitMQ..." -ForegroundColor Yellow
try {
    $testResult = rabbitmqctl status 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ RabbitMQ está funcionando correctamente" -ForegroundColor Green

        # Mostrar información básica
        Write-Host "   📊 Información del broker:" -ForegroundColor Gray
        rabbitmqctl list_queues 2>&1 | Select-Object -First 5 | ForEach-Object {
            Write-Host "      $_" -ForegroundColor Gray
        }
    } else {
        Write-Host "   ⚠️  No se pudo verificar el estado" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ⚠️  Error al verificar estado: $_" -ForegroundColor Yellow
}
Write-Host ""

# 5. Configuración opcional de usuario
Write-Host "5. Configuración de usuario (opcional)..." -ForegroundColor Yellow
$createUser = Read-Host "   ¿Quieres crear un usuario específico para Robot Runner? (s/n) [n]"

if ($createUser -eq "s" -or $createUser -eq "S") {
    Write-Host ""
    $username = Read-Host "   Nombre de usuario [robotrunner]"
    if ([string]::IsNullOrWhiteSpace($username)) {
        $username = "robotrunner"
    }

    $password = Read-Host "   Contraseña [robotpass]"
    if ([string]::IsNullOrWhiteSpace($password)) {
        $password = "robotpass"
    }

    try {
        # Crear usuario
        Write-Host "   🔄 Creando usuario..." -ForegroundColor Gray
        rabbitmqctl add_user $username $password 2>&1 | Out-Null

        # Dar permisos de administrador
        rabbitmqctl set_user_tags $username administrator 2>&1 | Out-Null

        # Dar permisos completos
        rabbitmqctl set_permissions -p / $username ".*" ".*" ".*" 2>&1 | Out-Null

        Write-Host "   ✅ Usuario creado: $username" -ForegroundColor Green
        Write-Host "   📝 Actualiza tu .env o config.json con:" -ForegroundColor Yellow
        Write-Host "      RABBITMQ_USER=$username" -ForegroundColor Gray
        Write-Host "      RABBITMQ_PASS=$password" -ForegroundColor Gray
    } catch {
        Write-Host "   ⚠️  Error al crear usuario: $_" -ForegroundColor Yellow
        Write-Host "   Puedes usar el usuario 'guest' por defecto" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ⏭️  Usando configuración por defecto (guest/guest)" -ForegroundColor Gray
}
Write-Host ""

# Resumen
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  ✅ RABBITMQ CONFIGURADO CORRECTAMENTE" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Información de conexión:" -ForegroundColor Cyan
Write-Host "   Host: localhost" -ForegroundColor White
Write-Host "   Puerto AMQP: 5672" -ForegroundColor White
Write-Host "   Puerto Management: 15672" -ForegroundColor White
Write-Host "   Usuario: guest (o el que hayas creado)" -ForegroundColor White
Write-Host ""
Write-Host "🌐 Interfaz web:" -ForegroundColor Cyan
Write-Host "   URL: http://localhost:15672" -ForegroundColor White
Write-Host ""
Write-Host "📝 Siguiente paso:" -ForegroundColor Cyan
Write-Host "   Ejecuta: cd ..\.. && python setup_tunnel.py" -ForegroundColor White
Write-Host "   (para configurar Cloudflare Tunnel)" -ForegroundColor White
Write-Host ""