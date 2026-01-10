#!/bin/bash
##############################################################################
# Instalación de dependencias para Robot Runner en Linux
#
# Instala:
# - Python 3.11
# - Git
# - Cloudflared
# - RabbitMQ Server
# - pip y virtualenv
##############################################################################

set -e

echo "======================================================================"
echo "  📦 INSTALACIÓN DE DEPENDENCIAS - ROBOT RUNNER LINUX"
echo "======================================================================"
echo ""

# Detectar distribución Linux
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VER=$VERSION_ID
else
    echo "❌ No se pudo detectar la distribución de Linux"
    exit 1
fi

echo "📋 Distribución detectada: $OS $VER"
echo ""

# Verificar permisos de sudo
if ! sudo -v; then
    echo "❌ Este script requiere permisos de sudo"
    exit 1
fi

echo "✅ Permisos de sudo verificados"
echo ""

# 1. Actualizar repositorios
echo "1. Actualizando repositorios..."
case $OS in
    ubuntu|debian)
        sudo apt-get update
        echo "   ✅ Repositorios actualizados"
        ;;
    fedora|rhel|centos)
        sudo dnf check-update || true
        echo "   ✅ Repositorios actualizados"
        ;;
    arch|manjaro)
        sudo pacman -Sy
        echo "   ✅ Repositorios actualizados"
        ;;
    *)
        echo "   ⚠️  Distribución no soportada automáticamente: $OS"
        echo "   Instala manualmente: Python 3.11, Git, RabbitMQ, Cloudflared"
        exit 1
        ;;
esac
echo ""

# 2. Instalar Python 3.11
echo "2. Instalando Python 3.11..."
if command -v python3.11 &> /dev/null; then
    PYTHON_VERSION=$(python3.11 --version)
    echo "   ✅ Python ya está instalado: $PYTHON_VERSION"
else
    case $OS in
        ubuntu|debian)
            sudo apt-get install -y python3.11 python3.11-venv python3-pip
            ;;
        fedora|rhel|centos)
            sudo dnf install -y python3.11 python3.11-pip
            ;;
        arch|manjaro)
            sudo pacman -S --noconfirm python python-pip
            ;;
    esac

    if command -v python3.11 &> /dev/null; then
        echo "   ✅ Python 3.11 instalado correctamente"
    else
        echo "   ⚠️  Python 3.11 no disponible, usando python3"
    fi
fi
echo ""

# 3. Instalar Git
echo "3. Instalando Git..."
if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version)
    echo "   ✅ Git ya está instalado: $GIT_VERSION"
else
    case $OS in
        ubuntu|debian)
            sudo apt-get install -y git
            ;;
        fedora|rhel|centos)
            sudo dnf install -y git
            ;;
        arch|manjaro)
            sudo pacman -S --noconfirm git
            ;;
    esac

    echo "   ✅ Git instalado correctamente"
fi
echo ""

# 4. Instalar Cloudflared
echo "4. Instalando Cloudflared..."
if command -v cloudflared &> /dev/null; then
    CLOUDFLARED_VERSION=$(cloudflared --version)
    echo "   ✅ Cloudflared ya está instalado: $CLOUDFLARED_VERSION"
else
    echo "   📥 Descargando Cloudflared..."

    case $OS in
        ubuntu|debian)
            # Descargar .deb
            wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
            sudo dpkg -i cloudflared-linux-amd64.deb
            rm cloudflared-linux-amd64.deb
            ;;
        fedora|rhel|centos)
            # Descargar .rpm
            wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-x86_64.rpm
            sudo rpm -i cloudflared-linux-x86_64.rpm
            rm cloudflared-linux-x86_64.rpm
            ;;
        *)
            # Instalación genérica
            wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
            sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared
            sudo chmod +x /usr/local/bin/cloudflared
            ;;
    esac

    echo "   ✅ Cloudflared instalado correctamente"
fi
echo ""

# 5. Instalar RabbitMQ (usando Docker - más simple y consistente)
echo "5. Instalando RabbitMQ..."

# Verificar si RabbitMQ ya está instalado
if systemctl is-active --quiet rabbitmq-server 2>/dev/null; then
    echo "   ✅ RabbitMQ ya está instalado y corriendo"
elif command -v docker &> /dev/null && docker ps --filter "name=rabbitmq" --format "{{.Names}}" | grep -q rabbitmq; then
    echo "   ✅ RabbitMQ ya está corriendo en Docker"
else
    echo "   🐳 Instalando RabbitMQ..."
    echo ""
    echo "   Opciones de instalación:"
    echo "   [1] Docker (recomendado - más fácil)"
    echo "   [2] Sistema (requiere configuración manual)"
    echo ""
    read -p "   Selecciona una opción [1]: " RABBITMQ_INSTALL_OPTION
    RABBITMQ_INSTALL_OPTION=${RABBITMQ_INSTALL_OPTION:-1}

    if [ "$RABBITMQ_INSTALL_OPTION" = "1" ]; then
        # Instalar con Docker
        if ! command -v docker &> /dev/null; then
            echo "   📦 Docker no está instalado, instalando..."
            case $OS in
                ubuntu|debian)
                    sudo apt-get install -y docker.io
                    sudo systemctl enable docker
                    sudo systemctl start docker
                    ;;
                fedora|rhel|centos)
                    sudo dnf install -y docker
                    sudo systemctl enable docker
                    sudo systemctl start docker
                    ;;
                arch|manjaro)
                    sudo pacman -S --noconfirm docker
                    sudo systemctl enable docker
                    sudo systemctl start docker
                    ;;
            esac
            sudo usermod -aG docker $USER
        fi

        echo "   🐰 Iniciando RabbitMQ en Docker..."
        sudo docker run -d \
            --name rabbitmq \
            --hostname rabbitmq \
            -p 5672:5672 \
            -p 15672:15672 \
            -e RABBITMQ_DEFAULT_USER=guest \
            -e RABBITMQ_DEFAULT_PASS=guest \
            --restart unless-stopped \
            rabbitmq:3-management

        sleep 5
        echo "   ✅ RabbitMQ instalado en Docker"
        echo "   🌐 Management UI: http://localhost:15672 (guest/guest)"
    else
        # Instalar en el sistema
        case $OS in
            ubuntu|debian)
                sudo apt-get install -y rabbitmq-server
                sudo systemctl enable rabbitmq-server
                sudo systemctl start rabbitmq-server
                ;;
            fedora|rhel|centos)
                sudo dnf install -y rabbitmq-server
                sudo systemctl enable rabbitmq-server
                sudo systemctl start rabbitmq-server
                ;;
            arch|manjaro)
                sudo pacman -S --noconfirm rabbitmq
                sudo systemctl enable rabbitmq
                sudo systemctl start rabbitmq
                ;;
        esac

        echo "   ✅ RabbitMQ instalado en el sistema"
    fi
fi
echo ""

# Resumen
echo "======================================================================"
echo "  ✅ INSTALACIÓN DE DEPENDENCIAS COMPLETADA"
echo "======================================================================"
echo ""
echo "📋 Componentes instalados:"
echo "   ✅ Python 3.11"
echo "   ✅ Git"
echo "   ✅ Cloudflared"
echo "   ✅ RabbitMQ Server"
echo ""
echo "📝 Siguiente paso:"
echo "   ./setup_python_env.sh"
echo ""