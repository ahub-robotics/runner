#!/bin/bash
##############################################################################
# Script maestro de instalación para Robot Runner en Linux
#
# Ejecuta todos los scripts de instalación en orden:
# 1. install_dependencies.sh - Instala herramientas del sistema
# 2. setup_python_env.sh - Configura Python y virtualenv
# 3. setup_rabbitmq.sh - Configura RabbitMQ
# 4. Opcionalmente: setup_tunnel.py - Configura Cloudflare Tunnel
##############################################################################

set -e

echo ""
echo "======================================================================"
echo "  🚀 INSTALACIÓN COMPLETA - ROBOT RUNNER LINUX"
echo "======================================================================"
echo ""
echo "Este script instalará y configurará:"
echo "  • Python 3.11"
echo "  • Git"
echo "  • Cloudflared"
echo "  • RabbitMQ (Docker o sistema)"
echo "  • Entorno virtual Python"
echo "  • Dependencias de Robot Runner (Celery, Flask, etc.)"
echo ""

read -p "¿Deseas continuar con la instalación? (s/n) [s]: " CONTINUE
if [ "$CONTINUE" = "n" ] || [ "$CONTINUE" = "N" ]; then
    echo "Instalación cancelada"
    exit 0
fi

echo ""
echo "======================================================================"
echo ""

# Obtener directorio del script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Dar permisos de ejecución a todos los scripts
chmod +x "$SCRIPT_DIR"/*.sh

# Paso 1: Instalar dependencias del sistema
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║  PASO 1/3: INSTALACIÓN DE DEPENDENCIAS DEL SISTEMA                ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

"$SCRIPT_DIR/install_dependencies.sh"

echo ""
read -p "Presiona Enter para continuar con el siguiente paso..."
echo ""

# Paso 2: Configurar entorno Python
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║  PASO 2/3: CONFIGURACIÓN DEL ENTORNO PYTHON                       ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

"$SCRIPT_DIR/setup_python_env.sh"

echo ""
read -p "Presiona Enter para continuar con el siguiente paso..."
echo ""

# Paso 3: Configurar RabbitMQ
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║  PASO 3/3: CONFIGURACIÓN DE RABBITMQ                              ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

"$SCRIPT_DIR/setup_rabbitmq.sh"

echo ""
echo "======================================================================"
echo "  ✅ INSTALACIÓN COMPLETADA CON ÉXITO"
echo "======================================================================"
echo ""

# Paso opcional: Cloudflare Tunnel
echo "📝 PASO OPCIONAL: Configurar Cloudflare Tunnel"
echo ""
read -p "¿Quieres configurar Cloudflare Tunnel ahora? (s/n) [n]: " SETUP_TUNNEL

if [ "$SETUP_TUNNEL" = "s" ] || [ "$SETUP_TUNNEL" = "S" ]; then
    echo ""
    echo "🌐 Configurando Cloudflare Tunnel..."
    echo ""

    PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
    TUNNEL_SCRIPT="$PROJECT_ROOT/setup_tunnel.py"

    if [ -f "$TUNNEL_SCRIPT" ]; then
        python3 "$TUNNEL_SCRIPT"
    else
        echo "⚠️  No se encontró setup_tunnel.py"
        echo "   Busca el script en la raíz del proyecto"
    fi
else
    echo ""
    echo "⏭️  Configuración de tunnel omitida"
    echo "   Para configurarlo más tarde, ejecuta:"
    echo "   python3 setup_tunnel.py"
fi

echo ""
echo "======================================================================"
echo "  🎉 ¡TODO LISTO!"
echo "======================================================================"
echo ""
echo "📋 Resumen de instalación:"
echo "   ✅ Dependencias del sistema instaladas"
echo "   ✅ Entorno Python configurado"
echo "   ✅ RabbitMQ configurado"
echo ""
echo "🚀 Para iniciar Robot Runner:"
echo "   1. Activa el virtualenv:"
echo "      source venv/bin/activate"
echo ""
echo "   2. Configura tu config.json con machine_id y token"
echo ""
echo "   3. Inicia el servidor:"
echo "      python main.py"
echo ""
echo "📖 Documentación adicional en el README.md"
echo ""