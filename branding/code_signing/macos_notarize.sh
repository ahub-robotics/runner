#!/bin/bash
# =================================================================
# macOS Code Signing & Notarization
# =================================================================
# Script profesional para firmar y notarizar aplicaciones macOS.
# Esto elimina la advertencia "App is from an unidentified developer"
#
# Requisitos:
#   - Apple Developer Account ($99 USD/año)
#   - Developer ID Application Certificate
#   - App-specific password para notarización
#   - Xcode Command Line Tools
#
# Uso:
#   ./macos_notarize.sh --app "dist/RobotRunner.app" \
#                       --bundle-id "com.ahubrobotics.robotrunner" \
#                       --apple-id "developer@ahubrobotics.com" \
#                       --team-id "TEAM_ID"
# =================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# =================================================================
# DEFAULT VALUES
# =================================================================
APP_PATH=""
BUNDLE_ID=""
APPLE_ID=""
TEAM_ID=""
APP_PASSWORD="@keychain:AC_PASSWORD"  # Almacenado en keychain
DRY_RUN=false

# =================================================================
# PARSE ARGUMENTS
# =================================================================
while [[ $# -gt 0 ]]; do
    case $1 in
        --app)
            APP_PATH="$2"
            shift 2
            ;;
        --bundle-id)
            BUNDLE_ID="$2"
            shift 2
            ;;
        --apple-id)
            APPLE_ID="$2"
            shift 2
            ;;
        --team-id)
            TEAM_ID="$2"
            shift 2
            ;;
        --password)
            APP_PASSWORD="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# =================================================================
# FUNCTIONS
# =================================================================

function print_header() {
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  🍎 macOS CODE SIGNING & NOTARIZATION${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
}

function print_guide() {
    echo -e "${YELLOW}📋 GUÍA DE CONFIGURACIÓN${NC}"
    echo ""

    echo -e "${CYAN}1️⃣  Unirse al Apple Developer Program:${NC}"
    echo "   https://developer.apple.com/programs/"
    echo "   💰 Costo: \$99 USD/año"
    echo ""

    echo -e "${CYAN}2️⃣  Crear certificado Developer ID Application:${NC}"
    echo "   a) Ir a: https://developer.apple.com/account/resources/certificates/list"
    echo "   b) Click '+' → Developer ID Application"
    echo "   c) Seguir las instrucciones para generar CSR"
    echo "   d) Descargar e instalar el certificado"
    echo ""

    echo -e "${CYAN}3️⃣  Crear App-Specific Password:${NC}"
    echo "   a) Ir a: https://appleid.apple.com/account/manage"
    echo "   b) App-Specific Passwords → Generate Password"
    echo "   c) Nombre: \"RobotRunner Notarization\""
    echo "   d) Guardar la contraseña"
    echo ""

    echo -e "${CYAN}4️⃣  Guardar password en keychain (recomendado):${NC}"
    echo '   xcrun notarytool store-credentials "AC_PASSWORD" \'
    echo '       --apple-id "developer@ahubrobotics.com" \'
    echo '       --team-id "TEAM_ID" \'
    echo '       --password "app-specific-password"'
    echo ""

    echo -e "${CYAN}5️⃣  Obtener Team ID:${NC}"
    echo "   a) Ir a: https://developer.apple.com/account/"
    echo "   b) Membership → Team ID"
    echo ""

    echo -e "${CYAN}6️⃣  Uso del script:${NC}"
    echo '   ./macos_notarize.sh \'
    echo '       --app "dist/RobotRunner.app" \'
    echo '       --bundle-id "com.ahubrobotics.robotrunner" \'
    echo '       --apple-id "developer@ahubrobotics.com" \'
    echo '       --team-id "YOUR_TEAM_ID"'
    echo ""

    echo -e "${CYAN}7️⃣  Configurar en GitHub Actions:${NC}"
    echo "   # En GitHub: Settings → Secrets"
    echo "   APPLE_ID: developer@ahubrobotics.com"
    echo "   APPLE_TEAM_ID: YOUR_TEAM_ID"
    echo "   APPLE_APP_PASSWORD: app-specific-password"
    echo "   APPLE_CERT_P12_BASE64: (certificado en base64)"
    echo "   APPLE_CERT_PASSWORD: (contraseña del certificado)"
    echo ""
}

function check_requirements() {
    echo -e "${CYAN}🔍 Verificando requisitos...${NC}"
    echo ""

    # Verificar Xcode Command Line Tools
    if ! xcode-select -p &> /dev/null; then
        echo -e "${RED}❌ Xcode Command Line Tools no instalados${NC}"
        echo -e "${YELLOW}   Instalar: xcode-select --install${NC}"
        return 1
    fi
    echo -e "${GREEN}✅ Xcode Command Line Tools instalados${NC}"

    # Verificar codesign
    if ! command -v codesign &> /dev/null; then
        echo -e "${RED}❌ codesign no disponible${NC}"
        return 1
    fi
    echo -e "${GREEN}✅ codesign disponible${NC}"

    # Verificar notarytool
    if ! xcrun notarytool --help &> /dev/null; then
        echo -e "${RED}❌ notarytool no disponible${NC}"
        echo -e "${YELLOW}   Actualizar Xcode Command Line Tools${NC}"
        return 1
    fi
    echo -e "${GREEN}✅ notarytool disponible${NC}"

    echo ""
    return 0
}

function list_certificates() {
    echo -e "${CYAN}📜 Certificados de firma disponibles:${NC}"
    echo ""
    security find-identity -v -p codesigning | grep "Developer ID Application" || echo "   No se encontraron certificados Developer ID"
    echo ""
}

function sign_app() {
    local app=$1
    local bundle_id=$2

    echo -e "${CYAN}🔐 Firmando aplicación...${NC}"
    echo "   App: $app"
    echo "   Bundle ID: $bundle_id"
    echo ""

    # Encontrar el certificado
    local cert=$(security find-identity -v -p codesigning | grep "Developer ID Application" | head -1 | awk -F'"' '{print $2}')

    if [ -z "$cert" ]; then
        echo -e "${RED}❌ No se encontró certificado Developer ID Application${NC}"
        return 1
    fi

    echo -e "${YELLOW}   Usando certificado: $cert${NC}"

    # Firmar con entitlements y opciones de seguridad
    codesign --force --deep \
        --options runtime \
        --sign "$cert" \
        --timestamp \
        "$app"

    # Verificar firma
    echo ""
    echo -e "${CYAN}🔍 Verificando firma...${NC}"
    codesign --verify --deep --strict --verbose=2 "$app"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Aplicación firmada correctamente${NC}"
        return 0
    else
        echo -e "${RED}❌ Error al firmar la aplicación${NC}"
        return 1
    fi
}

function notarize_app() {
    local app=$1
    local bundle_id=$2
    local apple_id=$3
    local team_id=$4
    local password=$5

    echo ""
    echo -e "${CYAN}📦 Creando archivo ZIP para notarización...${NC}"

    local zip_file="${app}.zip"
    ditto -c -k --keepParent "$app" "$zip_file"

    echo -e "${GREEN}✅ Archivo ZIP creado: $zip_file${NC}"
    echo ""

    echo -e "${CYAN}🚀 Enviando a Apple para notarización...${NC}"
    echo "   Esto puede tardar varios minutos..."
    echo ""

    # Notarizar usando notarytool
    xcrun notarytool submit "$zip_file" \
        --apple-id "$apple_id" \
        --team-id "$team_id" \
        --password "$password" \
        --wait

    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✅ Notarización exitosa${NC}"

        # Staple el ticket de notarización
        echo ""
        echo -e "${CYAN}📎 Agregando ticket de notarización...${NC}"
        xcrun stapler staple "$app"

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Ticket agregado correctamente${NC}"

            # Limpiar ZIP
            rm "$zip_file"

            return 0
        else
            echo -e "${RED}❌ Error al agregar ticket${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ Notarización fallida${NC}"
        echo ""
        echo "Para ver detalles del error:"
        echo "xcrun notarytool log <submission-id> --apple-id $apple_id --team-id $team_id --password $password"
        return 1
    fi
}

function verify_notarization() {
    local app=$1

    echo ""
    echo -e "${CYAN}🔍 Verificando notarización completa...${NC}"

    # Verificar que Gatekeeper lo acepte
    spctl --assess --verbose=4 --type execute "$app"

    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✅ La aplicación pasará las verificaciones de Gatekeeper${NC}"
        return 0
    else
        echo ""
        echo -e "${YELLOW}⚠️  La aplicación podría tener problemas con Gatekeeper${NC}"
        return 1
    fi
}

# =================================================================
# MAIN
# =================================================================

print_header

check_requirements || exit 1

# Modo dry-run - mostrar guía
if [ "$DRY_RUN" = true ] || [ -z "$APP_PATH" ]; then
    print_guide
    list_certificates
    exit 0
fi

# Verificar que existe la app
if [ ! -d "$APP_PATH" ] && [ ! -f "$APP_PATH" ]; then
    echo -e "${RED}❌ Aplicación no encontrada: $APP_PATH${NC}"
    exit 1
fi

# Verificar parámetros requeridos
if [ -z "$BUNDLE_ID" ] || [ -z "$APPLE_ID" ] || [ -z "$TEAM_ID" ]; then
    echo -e "${RED}❌ Faltan parámetros requeridos${NC}"
    echo ""
    echo "Uso:"
    echo "./macos_notarize.sh --app <path> --bundle-id <id> --apple-id <email> --team-id <team>"
    exit 1
fi

list_certificates

# Firmar
if ! sign_app "$APP_PATH" "$BUNDLE_ID"; then
    exit 1
fi

# Notarizar
if ! notarize_app "$APP_PATH" "$BUNDLE_ID" "$APPLE_ID" "$TEAM_ID" "$APP_PASSWORD"; then
    exit 1
fi

# Verificar
verify_notarization "$APP_PATH"

# Resumen
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ FIRMA Y NOTARIZACIÓN COMPLETADA${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${CYAN}📦 Aplicación lista para distribución:${NC}"
echo "   $APP_PATH"
echo ""
echo -e "${CYAN}🚀 Próximos pasos:${NC}"
echo "   1. Crear un DMG para distribución"
echo "   2. Subir a GitHub Releases"
echo "   3. Los usuarios podrán instalar sin alertas de seguridad"
echo ""