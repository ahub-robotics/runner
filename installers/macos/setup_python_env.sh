#!/bin/bash
##############################################################################
# Configuración del entorno Python para Robot Runner en macOS
#
# - Crea virtualenv
# - Instala dependencias de requirements.txt
# - Verifica paquetes críticos
##############################################################################

set -e

echo "======================================================================"
echo "  🐍 CONFIGURACIÓN DEL ENTORNO PYTHON - ROBOT RUNNER"
echo "======================================================================"
echo ""

# Obtener directorio del proyecto
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "📁 Directorio del proyecto: $PROJECT_ROOT"
echo ""

# 1. Verificar Python
echo "1. Verificando Python..."
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD=python3.11
elif command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
else
    echo "   ❌ Python no está instalado"
    echo "   Ejecuta primero: ./install_dependencies.sh"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version)
echo "   ✅ Python encontrado: $PYTHON_VERSION"
echo ""

# 2. Verificar requirements.txt
echo "2. Verificando requirements.txt..."
REQUIREMENTS_FILE="$PROJECT_ROOT/requirements.txt"
if [ ! -f "$REQUIREMENTS_FILE" ]; then
    echo "   ❌ No se encontró requirements.txt en: $REQUIREMENTS_FILE"
    exit 1
fi
echo "   ✅ requirements.txt encontrado"
echo ""

# 3. Crear virtualenv
echo "3. Creando virtualenv..."
VENV_PATH="$PROJECT_ROOT/venv"

if [ -d "$VENV_PATH" ]; then
    echo "   ⚠️  Virtualenv ya existe en: $VENV_PATH"
    read -p "   ¿Quieres recrearlo? (s/n) [n]: " RECREATE
    if [ "$RECREATE" = "s" ] || [ "$RECREATE" = "S" ]; then
        echo "   🗑️  Eliminando virtualenv anterior..."
        rm -rf "$VENV_PATH"
    else
        echo "   ⏭️  Usando virtualenv existente"
        echo ""
    fi
fi

if [ ! -d "$VENV_PATH" ]; then
    echo "   📦 Creando virtualenv en: $VENV_PATH"
    $PYTHON_CMD -m venv "$VENV_PATH"
    echo "   ✅ Virtualenv creado correctamente"
fi
echo ""

# 4. Instalar dependencias
echo "4. Instalando dependencias..."

# Activar virtualenv
source "$VENV_PATH/bin/activate"

# Actualizar pip
echo "   📦 Actualizando pip..."
pip install --upgrade pip > /dev/null

# Instalar dependencias
echo "   📦 Instalando dependencias desde requirements.txt..."
echo "      (esto puede tardar varios minutos)"
pip install -r "$REQUIREMENTS_FILE"

echo "   ✅ Dependencias instaladas correctamente"
echo ""

# 5. Verificar paquetes críticos
echo "5. Verificando paquetes críticos..."

CRITICAL_PACKAGES=("flask" "celery" "gunicorn" "pika" "pillow")
ALL_INSTALLED=true

for package in "${CRITICAL_PACKAGES[@]}"; do
    if python -c "import $package" 2>/dev/null; then
        echo "   ✅ $package"
    else
        echo "   ❌ $package - no instalado"
        ALL_INSTALLED=false
    fi
done
echo ""

# Desactivar virtualenv
deactivate

# Resumen
echo "======================================================================"
if [ "$ALL_INSTALLED" = true ]; then
    echo "  ✅ ENTORNO PYTHON CONFIGURADO CORRECTAMENTE"
else
    echo "  ⚠️  ENTORNO PYTHON CONFIGURADO CON ADVERTENCIAS"
fi
echo "======================================================================"
echo ""
echo "📋 Virtualenv:"
echo "   Ruta: $VENV_PATH"
echo "   Activar: source venv/bin/activate"
echo ""
echo "📝 Siguiente paso:"
echo "   ./setup_rabbitmq.sh"
echo ""