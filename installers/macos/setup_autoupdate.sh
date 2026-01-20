#!/bin/bash
# =================================================================
# Setup Auto-Update Service for Robot Runner (macOS)
# =================================================================
# Creates a launchd service that checks for updates periodically
#
# Usage:
#   ./setup_autoupdate.sh [--interval SECONDS] [--channel stable|beta|canary]
#
# Examples:
#   ./setup_autoupdate.sh
#   ./setup_autoupdate.sh --interval 1800 --channel beta
# =================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default values
INTERVAL=3600
CHANNEL="stable"
REPO="tu-usuario/robotrunner_windows"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --interval)
            INTERVAL="$2"
            shift 2
            ;;
        --channel)
            CHANNEL="$2"
            shift 2
            ;;
        --repo)
            REPO="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  🔄 CONFIGURACIÓN DE AUTO-ACTUALIZACIÓN (macOS)${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Get project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
UPDATE_SERVICE="$PROJECT_ROOT/update_service.py"

# Check if Python exists
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 no encontrado${NC}"
    exit 1
fi

PYTHON_PATH=$(which python3)

# Check if update_service.py exists
if [[ ! -f "$UPDATE_SERVICE" ]]; then
    echo -e "${RED}❌ No se encontró update_service.py en: $UPDATE_SERVICE${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python encontrado: $PYTHON_PATH${NC}"
echo -e "${GREEN}✅ Update service: $UPDATE_SERVICE${NC}"
echo ""

# Show configuration
INTERVAL_MIN=$((INTERVAL / 60))
echo -e "${CYAN}📋 Configuración:${NC}"
echo "   Intervalo: $INTERVAL segundos ($INTERVAL_MIN minutos)"
echo "   Canal: $CHANNEL"
echo "   Repositorio: $REPO"
echo ""

# Confirm
read -p "¿Deseas continuar? (s/n) [s]: " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Ss]$ ]] && [[ ! -z $REPLY ]]; then
    echo -e "${YELLOW}Configuración cancelada${NC}"
    exit 0
fi

echo ""
echo -e "${YELLOW}⚙️  Creando servicio launchd...${NC}"

# Create LaunchAgents directory if doesn't exist
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
mkdir -p "$LAUNCH_AGENTS_DIR"

# Service label and plist path
SERVICE_LABEL="com.robotrunner.autoupdate"
PLIST_FILE="$LAUNCH_AGENTS_DIR/$SERVICE_LABEL.plist"

# Create launchd plist file
cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$SERVICE_LABEL</string>

    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_PATH</string>
        <string>$UPDATE_SERVICE</string>
        <string>--interval</string>
        <string>$INTERVAL</string>
        <string>--channel</string>
        <string>$CHANNEL</string>
        <string>--repo</string>
        <string>$REPO</string>
    </array>

    <key>WorkingDirectory</key>
    <string>$PROJECT_ROOT</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>$HOME/Library/Logs/robotrunner-autoupdate.log</string>

    <key>StandardErrorPath</key>
    <string>$HOME/Library/Logs/robotrunner-autoupdate-error.log</string>
</dict>
</plist>
EOF

echo -e "${GREEN}✅ Archivo plist creado: $PLIST_FILE${NC}"

# Unload if already loaded
if launchctl list | grep -q "$SERVICE_LABEL"; then
    echo "🔄 Descargando servicio existente..."
    launchctl unload "$PLIST_FILE" 2>/dev/null || true
fi

# Load the service
echo "🔄 Cargando servicio..."
launchctl load "$PLIST_FILE"

# Wait a bit and check if running
sleep 2
if launchctl list | grep -q "$SERVICE_LABEL"; then
    echo ""
    echo -e "${GREEN}✅ Servicio iniciado correctamente${NC}"
else
    echo ""
    echo -e "${RED}❌ El servicio no se pudo iniciar${NC}"
    echo "Ver logs en: $HOME/Library/Logs/robotrunner-autoupdate.log"
    exit 1
fi

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ CONFIGURACIÓN COMPLETADA${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${CYAN}📋 El servicio de auto-actualización está activo:${NC}"
echo "   • Verifica actualizaciones cada $INTERVAL_MIN minutos"
echo "   • Se ejecuta automáticamente al iniciar sesión"
echo "   • Actualiza el ejecutable cuando hay nueva versión"
echo ""
echo -e "${CYAN}🔧 Comandos útiles:${NC}"
echo "   • Ver estado:"
echo "     launchctl list | grep $SERVICE_LABEL"
echo ""
echo "   • Ver logs:"
echo "     tail -f $HOME/Library/Logs/robotrunner-autoupdate.log"
echo ""
echo "   • Reiniciar servicio:"
echo "     launchctl unload $PLIST_FILE && launchctl load $PLIST_FILE"
echo ""
echo "   • Detener servicio:"
echo "     launchctl unload $PLIST_FILE"
echo ""
echo "   • Eliminar servicio:"
echo "     launchctl unload $PLIST_FILE && rm $PLIST_FILE"
echo ""
echo "📝 Logs en:"
echo "   • Output: $HOME/Library/Logs/robotrunner-autoupdate.log"
echo "   • Errors: $HOME/Library/Logs/robotrunner-autoupdate-error.log"
echo ""