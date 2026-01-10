#!/bin/bash
##############################################################################
# Instalación de dependencias para Robot Runner en macOS
#
# Instala:
# - Homebrew (si no está instalado)
# - Python 3.11
# - Git
# - Cloudflared
# - RabbitMQ Server
##############################################################################

set -e

echo "======================================================================"
echo "  📦 INSTALACIÓN DE DEPENDENCIAS - ROBOT RUNNER MACOS"
echo "======================================================================"
echo ""

echo "📋 Sistema operativo: $(sw_vers -productName) $(sw_vers -productVersion)"
echo ""

# 1. Verificar/Instalar Homebrew
echo "1. Verificando Homebrew..."
if command -v brew &> /dev/null; then
    BREW_VERSION=$(brew --version | head -n 1)
    echo "   ✅ Homebrew ya está instalado: $BREW_VERSION"
else
    echo "   📥 Instalando Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    # Agregar Homebrew al PATH
    if [[ $(uname -m) == 'arm64' ]]; then
        # Apple Silicon
        eval "$(/opt/homebrew/bin/brew shellenv)"
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
    else
        # Intel
        eval "$(/usr/local/bin/brew shellenv)"
        echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.bash_profile
    fi

    echo "   ✅ Homebrew instalado correctamente"
fi
echo ""

# Actualizar Homebrew
echo "   🔄 Actualizando Homebrew..."
brew update > /dev/null
echo "   ✅ Homebrew actualizado"
echo ""

# 2. Instalar Python 3.11
echo "2. Instalando Python 3.11..."
if brew list python@3.11 &> /dev/null; then
    PYTHON_VERSION=$(python3.11 --version)
    echo "   ✅ Python ya está instalado: $PYTHON_VERSION"
else
    echo "   📥 Instalando Python 3.11..."
    brew install python@3.11
    echo "   ✅ Python 3.11 instalado correctamente"
fi
echo ""

# 3. Instalar Git
echo "3. Verificando Git..."
if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version)
    echo "   ✅ Git ya está instalado: $GIT_VERSION"
else
    echo "   📥 Instalando Git..."
    brew install git
    echo "   ✅ Git instalado correctamente"
fi
echo ""

# 4. Instalar Cloudflared
echo "4. Instalando Cloudflared..."
if command -v cloudflared &> /dev/null; then
    CLOUDFLARED_VERSION=$(cloudflared --version)
    echo "   ✅ Cloudflared ya está instalado: $CLOUDFLARED_VERSION"
else
    echo "   📥 Instalando Cloudflared..."
    brew install cloudflared
    echo "   ✅ Cloudflared instalado correctamente"
fi
echo ""

# 5. Instalar RabbitMQ
echo "5. Instalando RabbitMQ..."

# Verificar si RabbitMQ ya está instalado
if brew list rabbitmq &> /dev/null; then
    echo "   ✅ RabbitMQ ya está instalado"

    # Verificar si está corriendo
    if brew services list | grep rabbitmq | grep -q started; then
        echo "   ✅ RabbitMQ está corriendo"
    else
        echo "   🔄 Iniciando RabbitMQ..."
        brew services start rabbitmq
        sleep 5
        echo "   ✅ RabbitMQ iniciado"
    fi
else
    echo "   📥 Instalando RabbitMQ..."
    brew install rabbitmq

    # Agregar RabbitMQ al PATH
    echo ""
    echo "   📝 Agregando RabbitMQ al PATH..."
    RABBITMQ_PATH="/opt/homebrew/opt/rabbitmq/sbin"
    if [[ $(uname -m) == 'x86_64' ]]; then
        RABBITMQ_PATH="/usr/local/opt/rabbitmq/sbin"
    fi

    if ! grep -q "$RABBITMQ_PATH" ~/.zprofile 2>/dev/null; then
        echo "export PATH=\"$RABBITMQ_PATH:\$PATH\"" >> ~/.zprofile
    fi
    export PATH="$RABBITMQ_PATH:$PATH"

    # Iniciar RabbitMQ
    echo "   🔄 Iniciando RabbitMQ..."
    brew services start rabbitmq
    sleep 5

    echo "   ✅ RabbitMQ instalado e iniciado"
fi
echo ""

# Resumen
echo "======================================================================"
echo "  ✅ INSTALACIÓN DE DEPENDENCIAS COMPLETADA"
echo "======================================================================"
echo ""
echo "📋 Componentes instalados:"
echo "   ✅ Homebrew"
echo "   ✅ Python 3.11"
echo "   ✅ Git"
echo "   ✅ Cloudflared"
echo "   ✅ RabbitMQ Server"
echo ""
echo "📝 Siguiente paso:"
echo "   ./setup_python_env.sh"
echo ""