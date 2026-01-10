#!/bin/bash
##############################################################################
# Configuración de RabbitMQ para Robot Runner en macOS
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

# Agregar RabbitMQ al PATH si no está
RABBITMQ_PATH="/opt/homebrew/opt/rabbitmq/sbin"
if [[ $(uname -m) == 'x86_64' ]]; then
    RABBITMQ_PATH="/usr/local/opt/rabbitmq/sbin"
fi
export PATH="$RABBITMQ_PATH:$PATH"

# 1. Verificar RabbitMQ
echo "1. Verificando RabbitMQ..."

if brew services list | grep rabbitmq | grep -q started; then
    echo "   ✅ RabbitMQ está corriendo"
else
    echo "   🔄 Iniciando RabbitMQ..."
    brew services start rabbitmq
    sleep 5
    echo "   ✅ RabbitMQ iniciado"
fi
echo ""

# 2. Habilitar plugin de management
echo "2. Habilitando RabbitMQ Management Plugin..."

if command -v rabbitmq-plugins &> /dev/null; then
    rabbitmq-plugins enable rabbitmq_management 2>/dev/null || true
    echo "   ✅ Plugin habilitado"
    echo "   🌐 Interfaz web: http://localhost:15672 (guest/guest)"
else
    echo "   ⚠️  rabbitmq-plugins no encontrado en PATH"
    echo "   Agrega al PATH: $RABBITMQ_PATH"
fi
echo ""

# 3. Verificar conectividad
echo "3. Verificando conectividad..."

if command -v rabbitmqctl &> /dev/null; then
    rabbitmqctl status > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "   ✅ RabbitMQ funcionando correctamente"

        # Mostrar información básica
        echo "   📊 Información del broker:"
        rabbitmqctl list_queues 2>/dev/null | head -n 5 | while read line; do
            echo "      $line"
        done
    else
        echo "   ⚠️  No se pudo verificar el estado"
    fi
else
    echo "   ⚠️  rabbitmqctl no encontrado en PATH"
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

    if command -v rabbitmqctl &> /dev/null; then
        # Crear usuario
        rabbitmqctl add_user "$USERNAME" "$PASSWORD" 2>/dev/null || true

        # Dar permisos de administrador
        rabbitmqctl set_user_tags "$USERNAME" administrator

        # Dar permisos completos
        rabbitmqctl set_permissions -p / "$USERNAME" ".*" ".*" ".*"

        echo "   ✅ Usuario creado: $USERNAME"
        echo ""
        echo "   📝 Actualiza tu .env o config.json con:"
        echo "      RABBITMQ_USER=$USERNAME"
        echo "      RABBITMQ_PASS=$PASSWORD"
    else
        echo "   ❌ No se pudo crear el usuario (rabbitmqctl no encontrado)"
    fi
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
echo "💡 Comandos útiles:"
echo "   Ver estado: brew services list | grep rabbitmq"
echo "   Iniciar: brew services start rabbitmq"
echo "   Detener: brew services stop rabbitmq"
echo ""
echo "📝 Siguiente paso:"
echo "   cd ../.. && python3 setup_tunnel.py"
echo "   (para configurar Cloudflare Tunnel)"
echo ""