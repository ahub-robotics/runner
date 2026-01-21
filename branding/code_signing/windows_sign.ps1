#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Firma código Windows con Authenticode

.DESCRIPTION
    Script profesional para firma de código de ejecutables Windows.
    Requiere un certificado de firma de código válido (.pfx)

.PARAMETER CertificatePath
    Ruta al archivo .pfx del certificado

.PARAMETER CertificatePassword
    Contraseña del certificado (si es SecureString mejor)

.PARAMETER FilesToSign
    Array de archivos a firmar

.PARAMETER TimestampServer
    URL del servidor de timestamp (por defecto: DigiCert)

.EXAMPLE
    .\windows_sign.ps1 -CertificatePath "cert.pfx" -CertificatePassword "password" -FilesToSign "dist/RobotRunner.exe"

.NOTES
    Requisitos:
    - Windows SDK (signtool.exe)
    - Certificado de firma de código válido

    Obtener certificado:
    - DigiCert: https://www.digicert.com/code-signing
    - Sectigo (Comodo): https://sectigo.com/ssl-certificates-tls/code-signing
    - GlobalSign: https://www.globalsign.com/en/code-signing-certificate

    Costo aproximado: $200-500 USD/año
#>

param(
    [Parameter(Mandatory=$false)]
    [string]$CertificatePath = "",

    [Parameter(Mandatory=$false)]
    [SecureString]$CertificatePassword,

    [Parameter(Mandatory=$false)]
    [string[]]$FilesToSign = @(),

    [Parameter(Mandatory=$false)]
    [string]$TimestampServer = "http://timestamp.digicert.com",

    [Parameter(Mandatory=$false)]
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

# =============================================================================
# FUNCIONES
# =============================================================================

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Test-SignTool {
    $signtool = Get-Command signtool.exe -ErrorAction SilentlyContinue
    if (-not $signtool) {
        Write-ColorOutput "❌ signtool.exe no encontrado" "Red"
        Write-ColorOutput "" "White"
        Write-ColorOutput "Instalar Windows SDK desde:" "Yellow"
        Write-ColorOutput "https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/" "Cyan"
        Write-ColorOutput "" "White"
        Write-ColorOutput "O usar scoop/chocolatey:" "Yellow"
        Write-ColorOutput "  scoop install windows-sdk" "Gray"
        Write-ColorOutput "  choco install windows-sdk" "Gray"
        return $false
    }
    return $true
}

function Get-CertificateInfo {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        Write-ColorOutput "❌ Certificado no encontrado: $Path" "Red"
        return $null
    }

    try {
        $cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($Path)
        return @{
            Subject = $cert.Subject
            Issuer = $cert.Issuer
            ValidFrom = $cert.NotBefore
            ValidTo = $cert.NotAfter
            Thumbprint = $cert.Thumbprint
        }
    }
    catch {
        Write-ColorOutput "⚠️  No se pudo leer info del certificado (requiere contraseña)" "Yellow"
        return $null
    }
}

function Sign-File {
    param(
        [string]$FilePath,
        [string]$CertPath,
        [SecureString]$CertPass,
        [string]$Timestamp
    )

    if (-not (Test-Path $FilePath)) {
        Write-ColorOutput "  ❌ Archivo no encontrado: $FilePath" "Red"
        return $false
    }

    Write-ColorOutput "  📝 Firmando: $(Split-Path -Leaf $FilePath)" "Cyan"

    # Convertir SecureString a plain text para signtool
    $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($CertPass)
    $PlainPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)

    try {
        # Ejecutar signtool
        $arguments = @(
            "sign",
            "/f", "`"$CertPath`"",
            "/p", "`"$PlainPassword`"",
            "/tr", $Timestamp,
            "/td", "sha256",
            "/fd", "sha256",
            "/v",
            "`"$FilePath`""
        )

        $processInfo = New-Object System.Diagnostics.ProcessStartInfo
        $processInfo.FileName = "signtool.exe"
        $processInfo.Arguments = $arguments -join " "
        $processInfo.UseShellExecute = $false
        $processInfo.RedirectStandardOutput = $true
        $processInfo.RedirectStandardError = $true

        $process = New-Object System.Diagnostics.Process
        $process.StartInfo = $processInfo
        $process.Start() | Out-Null
        $stdout = $process.StandardOutput.ReadToEnd()
        $stderr = $process.StandardError.ReadToEnd()
        $process.WaitForExit()

        if ($process.ExitCode -eq 0) {
            Write-ColorOutput "  ✅ Firmado exitosamente" "Green"
            return $true
        }
        else {
            Write-ColorOutput "  ❌ Error al firmar: $stderr" "Red"
            return $false
        }
    }
    finally {
        # Limpiar contraseña de memoria
        [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)
    }
}

function Verify-Signature {
    param([string]$FilePath)

    Write-ColorOutput "  🔍 Verificando firma..." "Cyan"

    $result = & signtool verify /pa /v "$FilePath" 2>&1

    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput "  ✅ Firma válida" "Green"
        return $true
    }
    else {
        Write-ColorOutput "  ❌ Firma inválida o no encontrada" "Red"
        return $false
    }
}

# =============================================================================
# MAIN
# =============================================================================

Write-ColorOutput "═══════════════════════════════════════════════════════════" "Cyan"
Write-ColorOutput "  🔐 FIRMA DE CÓDIGO WINDOWS (AUTHENTICODE)" "Cyan"
Write-ColorOutput "═══════════════════════════════════════════════════════════" "Cyan"
Write-ColorOutput "" "White"

# Verificar signtool
if (-not (Test-SignTool)) {
    exit 1
}

Write-ColorOutput "✅ signtool.exe encontrado" "Green"
Write-ColorOutput "" "White"

# Modo DryRun - mostrar guía
if ($DryRun -or -not $CertificatePath) {
    Write-ColorOutput "📋 GUÍA DE CONFIGURACIÓN" "Yellow"
    Write-ColorOutput "" "White"

    Write-ColorOutput "1️⃣  Obtener un certificado de firma de código:" "Cyan"
    Write-ColorOutput "   Proveedores recomendados:" "White"
    Write-ColorOutput "   • DigiCert: https://www.digicert.com/code-signing" "Gray"
    Write-ColorOutput "   • Sectigo: https://sectigo.com/ssl-certificates-tls/code-signing" "Gray"
    Write-ColorOutput "   • GlobalSign: https://www.globalsign.com/en/code-signing-certificate" "Gray"
    Write-ColorOutput "" "White"
    Write-ColorOutput "   💰 Costo: $200-500 USD/año" "Yellow"
    Write-ColorOutput "   ⏱️  Tiempo de emisión: 1-5 días hábiles" "Yellow"
    Write-ColorOutput "" "White"

    Write-ColorOutput "2️⃣  Guardar el certificado (.pfx) de forma segura:" "Cyan"
    Write-ColorOutput "   • No commitear al repositorio" "Yellow"
    Write-ColorOutput "   • Usar GitHub Secrets para CI/CD" "Yellow"
    Write-ColorOutput "   • Guardar en Azure Key Vault o similar" "Yellow"
    Write-ColorOutput "" "White"

    Write-ColorOutput "3️⃣  Configurar en GitHub Actions:" "Cyan"
    Write-ColorOutput "" "White"
    Write-ColorOutput "   # En GitHub: Settings → Secrets → New repository secret" "Gray"
    Write-ColorOutput "   WINDOWS_CERT_BASE64: (certificado .pfx en base64)" "Gray"
    Write-ColorOutput "   WINDOWS_CERT_PASSWORD: (contraseña del certificado)" "Gray"
    Write-ColorOutput "" "White"

    Write-ColorOutput "4️⃣  Uso del script:" "Cyan"
    Write-ColorOutput "" "White"
    Write-ColorOutput '   $password = ConvertTo-SecureString "password" -AsPlainText -Force' "Gray"
    Write-ColorOutput '   .\windows_sign.ps1 `' "Gray"
    Write-ColorOutput '       -CertificatePath "cert.pfx" `' "Gray"
    Write-ColorOutput '       -CertificatePassword $password `' "Gray"
    Write-ColorOutput '       -FilesToSign @("dist/RobotRunner.exe")' "Gray"
    Write-ColorOutput "" "White"

    Write-ColorOutput "5️⃣  Archivos a firmar:" "Cyan"
    Write-ColorOutput "   • dist/RobotRunner.exe (ejecutable principal)" "Gray"
    Write-ColorOutput "   • installers/*.exe (instaladores)" "Gray"
    Write-ColorOutput "   • dist/*.dll (DLLs si aplica)" "Gray"
    Write-ColorOutput "" "White"

    exit 0
}

# Verificar certificado
Write-ColorOutput "📜 Certificado:" "Cyan"
Write-ColorOutput "   Path: $CertificatePath" "White"

$certInfo = Get-CertificateInfo -Path $CertificatePath
if ($certInfo) {
    Write-ColorOutput "   Subject: $($certInfo.Subject)" "Gray"
    Write-ColorOutput "   Valid: $($certInfo.ValidFrom) → $($certInfo.ValidTo)" "Gray"
}
Write-ColorOutput "" "White"

# Firmar archivos
$totalFiles = $FilesToSign.Count
$signedFiles = 0

Write-ColorOutput "🔐 Firmando $totalFiles archivo(s)..." "Cyan"
Write-ColorOutput "" "White"

foreach ($file in $FilesToSign) {
    if (Sign-File -FilePath $file -CertPath $CertificatePath -CertPass $CertificatePassword -Timestamp $TimestampServer) {
        Verify-Signature -FilePath $file
        $signedFiles++
    }
    Write-ColorOutput "" "White"
}

# Resumen
Write-ColorOutput "═══════════════════════════════════════════════════════════" "Cyan"
if ($signedFiles -eq $totalFiles) {
    Write-ColorOutput "  ✅ TODOS LOS ARCHIVOS FIRMADOS EXITOSAMENTE" "Green"
}
else {
    Write-ColorOutput "  ⚠️  ALGUNOS ARCHIVOS NO SE PUDIERON FIRMAR" "Yellow"
    Write-ColorOutput "     Firmados: $signedFiles de $totalFiles" "Yellow"
}
Write-ColorOutput "═══════════════════════════════════════════════════════════" "Cyan"
Write-ColorOutput "" "White"

exit ($signedFiles -eq $totalFiles ? 0 : 1)