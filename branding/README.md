# 🎨 Branding & Code Signing

Sistema completo de branding, firma de código y notarización para Robot Runner.

## 📂 Estructura

```
branding/
├── app_metadata.json              # Metadatos de la aplicación
├── version_info.py                # Info de versión para Windows
├── macos_entitlements.plist       # Entitlements para macOS
├── generate_icons.sh              # Generador de iconos multiplataforma
│
├── icons/                         # Iconos generados
│   ├── windows/app.ico           # Windows 256x256
│   ├── macos/app.icns            # macOS 1024x1024
│   └── linux/app-{size}.png      # Linux múltiples tamaños
│
└── code_signing/                  # Scripts de firma de código
    ├── windows_sign.ps1          # Firma Authenticode (Windows)
    └── macos_notarize.sh         # Firma y notarización (macOS)
```

---

## 🚀 Quick Start

### 1. Generar Iconos

```bash
cd branding
./generate_icons.sh
```

**Requisitos:**
- ImageMagick: `brew install imagemagick`

**Output:**
- `icons/windows/app.ico` - Copiado a `resources/logo.ico`
- `icons/macos/app.icns` - Copiado a `resources/logo.icns`
- `icons/linux/app-{16,32,48,64,128,256,512}.png`

---

## 🔐 Firma de Código

### Windows (Authenticode)

**Requisitos:**
- Certificado de firma de código (.pfx)
- Windows SDK (signtool.exe)
- Costo: $200-500 USD/año

**Proveedores:**
- [DigiCert](https://www.digicert.com/code-signing)
- [Sectigo](https://sectigo.com/ssl-certificates-tls/code-signing)
- [GlobalSign](https://www.globalsign.com/en/code-signing-certificate)

**Uso:**

```powershell
# Modo dry-run (muestra guía)
.\code_signing\windows_sign.ps1 -DryRun

# Firmar ejecutable
$password = ConvertTo-SecureString "password" -AsPlainText -Force
.\code_signing\windows_sign.ps1 `
    -CertificatePath "cert.pfx" `
    -CertificatePassword $password `
    -FilesToSign @("dist/RobotRunner.exe")
```

**En GitHub Actions:**

```yaml
- name: Sign Windows executable
  env:
    CERT_PASSWORD: ${{ secrets.WINDOWS_CERT_PASSWORD }}
  run: |
    # Decodificar certificado desde base64
    echo "${{ secrets.WINDOWS_CERT_BASE64 }}" | base64 -d > cert.pfx

    # Firmar
    $password = ConvertTo-SecureString $env:CERT_PASSWORD -AsPlainText -Force
    .\branding\code_signing\windows_sign.ps1 `
        -CertificatePath "cert.pfx" `
        -CertificatePassword $password `
        -FilesToSign @("dist/RobotRunner-Windows-x64.exe")

    # Limpiar
    Remove-Item cert.pfx
```

---

### macOS (Notarization)

**Requisitos:**
- Apple Developer Account ($99 USD/año)
- Developer ID Application Certificate
- App-specific password
- Xcode Command Line Tools

**Setup:**

1. **Obtener certificado:**
   - https://developer.apple.com/account/resources/certificates/list
   - Crear "Developer ID Application"

2. **App-specific password:**
   - https://appleid.apple.com/account/manage
   - Generar password
   - Guardar en keychain:
     ```bash
     xcrun notarytool store-credentials "AC_PASSWORD" \
         --apple-id "developer@ahubrobotics.com" \
         --team-id "YOUR_TEAM_ID" \
         --password "app-specific-password"
     ```

**Uso:**

```bash
# Modo dry-run (muestra guía)
./code_signing/macos_notarize.sh --dry-run

# Firmar y notarizar
./code_signing/macos_notarize.sh \
    --app "dist/RobotRunner.app" \
    --bundle-id "com.ahubrobotics.robotrunner" \
    --apple-id "developer@ahubrobotics.com" \
    --team-id "YOUR_TEAM_ID"
```

**En GitHub Actions:**

```yaml
- name: Sign & Notarize macOS app
  env:
    APPLE_ID: ${{ secrets.APPLE_ID }}
    APPLE_TEAM_ID: ${{ secrets.APPLE_TEAM_ID }}
    APPLE_APP_PASSWORD: ${{ secrets.APPLE_APP_PASSWORD }}
  run: |
    # Importar certificado
    echo "${{ secrets.APPLE_CERT_P12_BASE64 }}" | base64 -d > cert.p12
    security create-keychain -p actions temp.keychain
    security import cert.p12 -k temp.keychain -P "${{ secrets.APPLE_CERT_PASSWORD }}" -T /usr/bin/codesign
    security set-key-partition-list -S apple-tool:,apple: -s -k actions temp.keychain

    # Firmar y notarizar
    ./branding/code_signing/macos_notarize.sh \
        --app "dist/RobotRunner-macOS-x64" \
        --bundle-id "com.ahubrobotics.robotrunner" \
        --apple-id "$APPLE_ID" \
        --team-id "$APPLE_TEAM_ID" \
        --password "$APPLE_APP_PASSWORD"
```

---

## 📝 Metadatos de la Aplicación

Editar `app_metadata.json` para cambiar:

- **Nombre de la empresa**
- **Copyright**
- **Website/Support**
- **Bundle IDs**
- **Versión**

```json
{
  "name": "Robot Runner",
  "company": "AHUB Robotics",
  "copyright": "Copyright © 2026 AHUB Robotics. All rights reserved.",
  "version": "2.0.0",
  "bundle_id": "com.ahubrobotics.robotrunner"
}
```

---

## 🔄 CI/CD Integration

### GitHub Secrets Necesarios

**Windows:**
- `WINDOWS_CERT_BASE64` - Certificado .pfx en base64
- `WINDOWS_CERT_PASSWORD` - Contraseña del certificado

**macOS:**
- `APPLE_ID` - Email del Apple Developer
- `APPLE_TEAM_ID` - Team ID (10 caracteres)
- `APPLE_APP_PASSWORD` - App-specific password
- `APPLE_CERT_P12_BASE64` - Certificado .p12 en base64
- `APPLE_CERT_PASSWORD` - Contraseña del certificado

### Workflow Completo

```yaml
jobs:
  build-and-sign:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [windows-latest, macos-latest, ubuntu-latest]

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Build
        run: pyinstaller app-onefile.spec

      - name: Sign (Windows)
        if: matrix.os == 'windows-latest'
        run: |
          # Firma con Authenticode

      - name: Sign & Notarize (macOS)
        if: matrix.os == 'macos-latest'
        run: |
          # Firma y notarización

      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          files: dist/*
```

---

## 📊 Costos de Firma de Código

| Plataforma | Tipo | Costo Anual | Proveedor |
|------------|------|-------------|-----------|
| **Windows** | Code Signing Certificate | $200-500 | DigiCert, Sectigo, GlobalSign |
| **macOS** | Apple Developer Program | $99 | Apple |
| **Linux** | GPG (opcional) | Gratis | - |

**Total:** ~$300-600 USD/año para firma completa en Windows + macOS

---

## ✅ Checklist de Distribución

### Antes de la Release:

- [ ] Generar iconos con `generate_icons.sh`
- [ ] Actualizar versión en `app_metadata.json`
- [ ] Obtener certificados de firma (Windows, macOS)
- [ ] Configurar secrets en GitHub
- [ ] Probar firma localmente
- [ ] Verificar que PyInstaller usa los metadatos correctos

### Durante la Release:

- [ ] Compilar binarios en CI/CD
- [ ] Firmar ejecutables automáticamente
- [ ] Notarizar app de macOS
- [ ] Generar checksums SHA256
- [ ] Crear instaladores profesionales
- [ ] Probar instalación en máquinas limpias

### Después de la Release:

- [ ] Verificar que no aparecen alertas de seguridad
- [ ] Probar auto-actualización
- [ ] Monitorear reportes de usuarios
- [ ] Documentar problemas conocidos

---

## 🐛 Troubleshooting

### Windows: "Publisher: Unknown"

**Causa:** Ejecutable no firmado o firma inválida

**Solución:**
1. Verificar que el certificado es válido
2. Re-firmar con signtool
3. Verificar: `signtool verify /pa dist/RobotRunner.exe`

### macOS: "App is from an unidentified developer"

**Causa:** App no notarizada o firma incorrecta

**Solución:**
1. Verificar firma: `codesign --verify --deep --verbose=2 app.app`
2. Verificar notarización: `spctl --assess --verbose=4 app.app`
3. Re-notarizar si es necesario

### Linux: No hay alertas de seguridad

Linux generalmente no requiere firma para aplicaciones de escritorio.
Opcionalmente puedes firmar con GPG para verificación de integridad.

---

## 📚 Referencias

- [Apple Notarization Guide](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)
- [Windows Code Signing](https://docs.microsoft.com/en-us/windows/win32/seccrypto/signtool)
- [PyInstaller Docs](https://pyinstaller.org/)

---

**Última actualización:** 2026-01-21
**Versión:** 1.0.0
