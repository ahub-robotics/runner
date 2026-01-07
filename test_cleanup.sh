#!/bin/bash
# Test script para verificar que el cleanup automático de Celery funciona

echo "=========================================="
echo "TEST: Cleanup Automático de Celery"
echo "=========================================="
echo ""

# Paso 1: Verificar procesos actuales
echo "[1] Procesos actuales:"
ps aux | grep -E "(celery.*src.celery_config|python.*app.run)" | grep -v grep || echo "  (ninguno)"
echo ""

# Paso 2: Detener el servidor Flask
FLASK_PID=$(ps aux | grep "python.*app.run" | grep -v grep | awk '{print $2}')
if [ -z "$FLASK_PID" ]; then
    echo "[2] No hay servidor Flask corriendo"
    exit 1
fi

echo "[2] Deteniendo Flask server (PID: $FLASK_PID)..."
kill -SIGTERM $FLASK_PID
echo ""

# Paso 3: Esperar a que el cleanup se ejecute
echo "[3] Esperando 3 segundos para que el cleanup se ejecute..."
sleep 3
echo ""

# Paso 4: Verificar que los workers de Celery fueron terminados
echo "[4] Verificando que los workers de Celery fueron terminados..."
CELERY_PIDS=$(ps aux | grep "celery.*src.celery_config" | grep -v grep | awk '{print $2}')

if [ -z "$CELERY_PIDS" ]; then
    echo "  ✅ Workers de Celery terminados correctamente"
    echo ""
    echo "=========================================="
    echo "TEST EXITOSO"
    echo "=========================================="
    exit 0
else
    echo "  ❌ Workers de Celery aún corriendo: $CELERY_PIDS"
    echo ""
    echo "=========================================="
    echo "TEST FALLIDO"
    echo "=========================================="
    exit 1
fi