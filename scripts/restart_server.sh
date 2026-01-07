#!/bin/bash
# Script para reiniciar el servidor de Robot Runner

echo "🔄 Reiniciando Robot Runner..."
echo ""

# Obtener el directorio del proyecto
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$PROJECT_DIR"

# 1. Detener procesos actuales
echo "1️⃣  Deteniendo procesos actuales..."
pkill -f "run.py --server-only" 2>/dev/null
sleep 2

# Verificar que se detuvieron
if pgrep -f "run.py --server-only" > /dev/null; then
    echo "⚠️  Algunos procesos no se detuvieron, forzando..."
    pkill -9 -f "run.py --server-only" 2>/dev/null
    sleep 1
fi

# 2. Limpiar estado de streaming en Redis
echo ""
echo "2️⃣  Limpiando estado de streaming..."
redis-cli -p 6378 DEL streaming:state > /dev/null 2>&1
redis-cli -p 6378 DEL streaming:stop_requested > /dev/null 2>&1

# 3. Verificar que Redis está corriendo
echo ""
echo "3️⃣  Verificando Redis..."
if redis-cli -p 6378 ping > /dev/null 2>&1; then
    echo "   ✅ Redis está corriendo"
else
    echo "   ❌ Redis no está corriendo. Iniciando..."
    redis-server --port 6378 --daemonize yes
    sleep 2
fi

# 4. Iniciar servidor
echo ""
echo "4️⃣  Iniciando servidor..."
nohup python run.py --server-only > logs/server.log 2>&1 &
SERVER_PID=$!

echo "   Servidor iniciado (PID: $SERVER_PID)"
echo "   Esperando a que esté listo..."
sleep 3

# 5. Verificar que arrancó correctamente
if ps -p $SERVER_PID > /dev/null; then
    echo "   ✅ Servidor corriendo"

    # Verificar workers de Celery
    echo ""
    echo "5️⃣  Verificando workers de Celery..."
    sleep 2

    python << EOF
from src.celery_config import celery_app
import sys

try:
    inspect = celery_app.control.inspect()
    stats = inspect.stats()

    if stats:
        print(f"   ✅ Workers activos: {len(stats)}")

        # Verificar tareas de streaming
        registered = celery_app.control.inspect().registered()
        if registered:
            for worker, tasks in registered.items():
                streaming_tasks = [t for t in tasks if 'streaming_tasks' in t]
                if streaming_tasks:
                    print(f"   ✅ Tareas de streaming registradas: {len(streaming_tasks)}")
                    for task in streaming_tasks:
                        print(f"      - {task}")
                else:
                    print(f"   ⚠️  No se encontraron tareas de streaming")
                    sys.exit(1)
    else:
        print("   ⚠️  No hay workers activos")
        sys.exit(1)
except Exception as e:
    print(f"   ❌ Error verificando workers: {e}")
    sys.exit(1)
EOF

    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Servidor reiniciado exitosamente"
        echo ""
        echo "📊 Información:"
        echo "   - URL: https://localhost:5055"
        echo "   - Streaming: https://localhost:5055/stream-view"
        echo "   - Logs: tail -f logs/server.log"
        echo ""
        echo "🎬 Prueba el streaming:"
        echo "   1. Navega a https://localhost:5055/stream-view"
        echo "   2. Click en 'Iniciar'"
        echo "   3. Deberías ver tu pantalla"
    else
        echo ""
        echo "⚠️  Servidor iniciado pero hay problemas con Celery"
        echo "   Revisa los logs: tail -f logs/server.log"
    fi
else
    echo "   ❌ Error al iniciar el servidor"
    echo "   Revisa los logs: tail -f logs/server.log"
    exit 1
fi
