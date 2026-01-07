#!/bin/bash
################################################################################
# Start Server - Script para iniciar el servidor con verificación previa
################################################################################
#
# Descripción:
#   Inicia el servidor Robot Runner con las siguientes verificaciones:
#   1. Verifica si hay procesos de Gunicorn corriendo
#   2. Si hay procesos, pregunta si detenerlos
#   3. Inicia el servidor en el modo seleccionado
#
# Uso:
#   ./scripts/start_server.sh                # Con GUI (modo normal)
#   ./scripts/start_server.sh --server-only  # Sin GUI
#   ./scripts/start_server.sh --force        # Fuerza inicio matando procesos
#
################################################################################

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Directorio del proyecto (un nivel arriba de scripts/)
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "======================================================================"
echo "  Robot Runner - Inicio del Servidor"
echo "======================================================================"
echo ""

# Verificar si hay procesos de Gunicorn corriendo
PIDS=$(ps aux | grep '[g]unicorn' | grep -v grep | awk '{print $2}')

if [ -n "$PIDS" ]; then
    COUNT=$(echo "$PIDS" | wc -w | tr -d ' ')
    echo -e "${YELLOW}⚠️  Atención: Hay $COUNT proceso(s) de Gunicorn corriendo${NC}"
    echo ""
    echo "PIDs: $PIDS"
    echo ""

    # Si se pasa --force, matar automáticamente
    if [ "$1" = "--force" ] || [ "$2" = "--force" ]; then
        echo "🔧 Modo --force activado. Deteniendo procesos..."
        "$PROJECT_DIR/scripts/kill_gunicorn.sh"
        sleep 1
    else
        # Preguntar al usuario
        read -p "¿Deseas detener estos procesos antes de continuar? (s/n): " -n 1 -r
        echo ""

        if [[ $REPLY =~ ^[SsYy]$ ]]; then
            echo "🔧 Deteniendo procesos..."
            "$PROJECT_DIR/scripts/kill_gunicorn.sh"
            sleep 1
        else
            echo -e "${RED}❌ No se puede iniciar el servidor con procesos corriendo${NC}"
            echo ""
            echo "Opciones:"
            echo "  1. Ejecuta: ./scripts/kill_gunicorn.sh"
            echo "  2. O usa:   ./scripts/start_server.sh --force"
            exit 1
        fi
    fi
fi

echo ""
echo "======================================================================"
echo "  Iniciando servidor..."
echo "======================================================================"
echo ""

# Cambiar al directorio del proyecto
cd "$PROJECT_DIR" || exit 1

# Determinar modo de ejecución
if [ "$1" = "--server-only" ] || [ "$2" = "--server-only" ]; then
    echo "🚀 Modo: Solo servidor (sin GUI)"
    echo ""
    python run.py --server-only
else
    echo "🚀 Modo: Servidor + GUI"
    echo ""
    python run.py
fi