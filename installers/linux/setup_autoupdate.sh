#!/bin/bash
# =================================================================
# Setup Auto-Update Service for Robot Runner (Linux)
# =================================================================
# Creates a systemd service that checks for updates periodically
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
echo -e "${CYAN}  🔄 CONFIGURACIÓN DE AUTO-ACTUALIZACIÓN (Linux)${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}❌ Este script debe ejecutarse como root (sudo)${NC}"
   exit 1
fi

# Get project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
UPDATE_SERVICE="$PROJECT_ROOT/update_service.py"

# Check if Python exists
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 no encontrado${NC}"
    exit 1
fi

# Check if update_service.py exists
if [[ ! -f "$UPDATE_SERVICE" ]]; then
    echo -e "${RED}❌ No se encontró update_service.py en: $UPDATE_SERVICE${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python encontrado: $(which python3)${NC}"
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
echo -e "${YELLOW}⚙️  Creando servicio systemd...${NC}"

# Create systemd service file
SERVICE_FILE="/etc/systemd/system/robotrunner-autoupdate.service"

cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Robot Runner Auto-Update Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_ROOT
ExecStart=$(which python3) $UPDATE_SERVICE --interval $INTERVAL --channel $CHANNEL --repo $REPO
Restart=always
RestartSec=60

# Logging
StandardOutput=append:/var/log/robotrunner-autoupdate.log
StandardError=append:/var/log/robotrunner-autoupdate.log

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✅ Archivo de servicio creado: $SERVICE_FILE${NC}"

# Reload systemd
echo "🔄 Recargando systemd..."
systemctl daemon-reload

# Enable service
echo "🔄 Habilitando servicio..."
systemctl enable robotrunner-autoupdate.service

# Start service
echo "▶️  Iniciando servicio..."
systemctl start robotrunner-autoupdate.service

# Check status
sleep 2
if systemctl is-active --quiet robotrunner-autoupdate.service; then
    echo ""
    echo -e "${GREEN}✅ Servicio iniciado correctamente${NC}"
else
    echo ""
    echo -e "${RED}❌ El servicio no se pudo iniciar${NC}"
    echo "Ver logs con: journalctl -u robotrunner-autoupdate.service -f"
    exit 1
fi

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ CONFIGURACIÓN COMPLETADA${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${CYAN}📋 El servicio de auto-actualización está activo:${NC}"
echo "   • Verifica actualizaciones cada $INTERVAL_MIN minutos"
echo "   • Se ejecuta automáticamente al iniciar el sistema"
echo "   • Actualiza el ejecutable cuando hay nueva versión"
echo ""
echo -e "${CYAN}🔧 Comandos útiles:${NC}"
echo "   • Ver estado:"
echo "     sudo systemctl status robotrunner-autoupdate"
echo ""
echo "   • Ver logs en tiempo real:"
echo "     sudo journalctl -u robotrunner-autoupdate -f"
echo ""
echo "   • Reiniciar servicio:"
echo "     sudo systemctl restart robotrunner-autoupdate"
echo ""
echo "   • Detener servicio:"
echo "     sudo systemctl stop robotrunner-autoupdate"
echo ""
echo "   • Desactivar auto-actualización:"
echo "     sudo systemctl disable robotrunner-autoupdate"
echo ""
echo "📝 Logs en: /var/log/robotrunner-autoupdate.log"
echo ""