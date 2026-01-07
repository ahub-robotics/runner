#!/bin/bash
# Test final de cleanup automático con la nueva configuración

echo "=========================================="
echo "TEST FINAL: Cleanup con celery_app.control.shutdown()"
echo "=========================================="
echo ""

# Paso 1: Verificar procesos actuales
echo "[1] Procesos actuales:"
echo "  Flask server:"
ps aux | grep "python.*app.run" | grep -v grep | awk '{print "    PID:", $2}'
echo "  Celery workers:"
ps aux | grep "celery.*src.celery_config" | grep -v grep | awk '{print "    PID:", $2}'
echo ""

# Paso 2: Detener el servidor Flask
FLASK_PID=$(ps aux | grep "python.*app.run" | grep -v grep | awk '{print $2}')
if [ -z "$FLASK_PID" ]; then
    echo "[2] ❌ No hay servidor Flask corriendo"
    exit 1
fi

echo "[2] Deteniendo Flask server (PID: $FLASK_PID)..."
kill -SIGTERM $FLASK_PID
echo ""

# Paso 3: Esperar y observar el cleanup
echo "[3] Esperando cleanup automático..."
echo "  (El cleanup ahora usa celery_app.control.shutdown() primero)"
sleep 8  # Esperar 8 segundos (5 para shutdown + 3 de margen)
echo ""

# Paso 4: Verificar que los workers fueron terminados
echo "[4] Verificando que los workers de Celery fueron terminados..."
CELERY_PIDS=$(ps aux | grep "celery.*src.celery_config" | grep -v grep | awk '{print $2}')

if [ -z "$CELERY_PIDS" ]; then
    echo "  ✅ Workers de Celery terminados correctamente"
    echo ""
    echo "=========================================="
    echo "TEST EXITOSO"
    echo "=========================================="
    echo "La función cleanup_celery_workers() ahora:"
    echo "  1. Usa celery_app.control.shutdown() (grácil)"
    echo "  2. Espera 5 segundos"
    echo "  3. Si quedan, envía SIGTERM"
    echo "  4. Si aún quedan, fuerza con SIGKILL"
    echo ""
    echo "Esto sigue el mismo patrón que:"
    echo "  - celery_worker.py:70 (control.shutdown)"
    echo "  - redis_manager.py:181 (terminate + wait + kill)"
    exit 0
else
    echo "  ❌ Workers de Celery aún corriendo: $CELERY_PIDS"
    echo ""
    echo "=========================================="
    echo "TEST FALLIDO"
    echo "=========================================="
    exit 1
fi