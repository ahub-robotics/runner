#!/bin/bash
################################################################################
# Start Tray App - Inicia la aplicación de System Tray
################################################################################
#
# Uso:
#   ./start_tray.sh
#
################################################################################

echo "========================================================================"
echo "  Iniciando Robot Runner System Tray App"
echo "========================================================================"
echo ""

# Verificar si ya está corriendo
if pgrep -f "tray_app.py" > /dev/null; then
    echo "⚠️  La aplicación del tray ya está corriendo"
    echo ""
    echo "Para detenerla:"
    echo "   pkill -f tray_app.py"
    echo ""
    exit 1
fi

# Iniciar la aplicación
echo "🚀 Iniciando aplicación..."
python tray_app.py &

# Esperar un momento
sleep 2

# Verificar que se inició
if pgrep -f "tray_app.py" > /dev/null; then
    echo "✅ Aplicación iniciada correctamente"
    echo ""
    echo "Busca el icono en la bandeja del sistema (barra de menú superior)"
    echo "Haz clic derecho en el icono para ver las opciones"
    echo ""
else
    echo "❌ Error al iniciar la aplicación"
    exit 1
fi