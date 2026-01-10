#!/bin/bash
##############################################################################
# Configuración de RabbitMQ para Robot Runner en Linux
#
# - Verifica servicio RabbitMQ
# - Habilita plugin de management
# - Configura usuario (opcional)
##############################################################################

set -e

echo "======================================================================"
echo "  🐰 CONFIGURACIÓN DE RABBITMQ - ROBOT RUNNER"
echo "======================================================================"
echo ""

# 1. Verificar RabbitMQ
echo "1. Verificando RabbitMQ..."

RABBITMQ_RUNNING=false

# Verificar servicio systemd
if systemctl is-active --quiet rabbitmq-server 2>/dev/null; then
    echo "   ✅ RabbitMQ (sistema) está corriendo"
    RABBITMQ_TYPE="system"
    RABBITMQ_RUNNING=true
# Verificar Docker
elif command -v docker &> /dev/null && docker ps --filter "name=rabbitmq" --format "{{.Names}}" | grep -q rabbitmq; then
    echo "   ✅ RabbitMQ (Docker) está corriendo"
    RABBITMQ_TYPE="docker"
    RABBITMQ_RUNNING=true
else
    echo "   ❌ RabbitMQ no está corriendo"
    echo "   Ejecuta primero: ./install_dependencies.sh"
    exit 1
fi
echo ""

# 2. Habilitar plugin de management
echo "2. Habilitando RabbitMQ Management Plugin..."

if [ "$RABBITMQ_TYPE" = "system" ]; then
    # Sistema: usar rabbitmq-plugins
    if command -v rabbitmq-plugins &> /dev/null; then
        sudo rabbitmq-plugins enable rabbitmq_management 2>/dev/null || true
        echo "   ✅ Plugin habilitado"
        echo "   🌐 Interfaz web: http://localhost:15672 (guest/guest)"
    else
        echo "   ⚠️  rabbitmq-plugins no encontrado"
    fi
elif [ "$RABBITMQ_TYPE" = "docker" ]; then
    # Docker: el plugin ya está habilitado en la imagen rabbitmq:management
    echo "   ✅ Plugin ya habilitado (imagen management)"
    echo "   🌐 Interfaz web: http://localhost:15672 (guest/guest)"
fi
echo ""

# 3. Verificar conectividad
echo "3. Verificando conectividad..."

if [ "$RABBITMQ_TYPE" = "system" ]; then
    if command -v rabbitmqctl &> /dev/null; then
        sudo rabbitmqctl status > /dev/null 2>&1
        if [ $? -eq 0 ]; then
            echo "   ✅ RabbitMQ funcionando correctamente"
        else
            echo "   ⚠️  No se pudo verificar el estado"
        fi
    fi
elif [ "$RABBITMQ_TYPE" = "docker" ]; then
    # Verificar que el contenedor responde
    if docker exec rabbitmq rabbitmqctl status > /dev/null 2>&1; then
        echo "   ✅ RabbitMQ funcionando correctamente"
    else
        echo "   ⚠️  No se pudo verificar el estado"
    fi
fi
echo ""

# 4. Configuración de usuario (opcional)
echo "4. Configuración de usuario (opcional)..."
read -p "   ¿Quieres crear un usuario específico para Robot Runner? (s/n) [n]: " CREATE_USER

if [ "$CREATE_USER" = "s" ] || [ "$CREATE_USER" = "S" ]; then
    echo ""
    read -p "   Nombre de usuario [robotrunner]: " USERNAME
    USERNAME=${USERNAME:-robotrunner}

    read -s -p "   Contraseña [robotpass]: " PASSWORD
    echo ""
    PASSWORD=${PASSWORD:-robotpass}

    echo ""
    echo "   🔄 Creando usuario..."

    if [ "$RABBITMQ_TYPE" = "system" ]; then
        # Sistema: usar rabbitmqctl
        sudo rabbitmqctl add_user "$USERNAME" "$PASSWORD" 2>/dev/null || true
        sudo rabbitmqctl set_user_tags "$USERNAME" administrator
        sudo rabbitmqctl set_permissions -p / "$USERNAME" ".*" ".*" ".*"
    elif [ "$RABBITMQ_TYPE" = "docker" ]; then
        # Docker: usar docker exec
        docker exec rabbitmq rabbitmqctl add_user "$USERNAME" "$PASSWORD" 2>/dev/null || true
        docker exec rabbitmq rabbitmqctl set_user_tags "$USERNAME" administrator
        docker exec rabbitmq rabbitmqctl set_permissions -p / "$USERNAME" ".*" ".*" ".*"
    fi

    echo "   ✅ Usuario creado: $USERNAME"
    echo ""
    echo "   📝 Actualiza tu .env o config.json con:"
    echo "      RABBITMQ_USER=$USERNAME"
    echo "      RABBITMQ_PASS=$PASSWORD"
else
    echo "   ⏭️  Usando configuración por defecto (guest/guest)"
fi
echo ""

# Resumen
echo "======================================================================"
echo "  ✅ RABBITMQ CONFIGURADO CORRECTAMENTE"
echo "======================================================================"
echo ""
echo "📋 Información de conexión:"
echo "   Host: localhost"
echo "   Puerto AMQP: 5672"
echo "   Puerto Management: 15672"
echo "   Usuario: guest (o el que hayas creado)"
echo ""
echo "🌐 Interfaz web:"
echo "   URL: http://localhost:15672"
echo ""
echo "📝 Siguiente paso:"
echo "   cd ../.. && python setup_tunnel.py"
echo "   (para configurar Cloudflare Tunnel)"
echo ""