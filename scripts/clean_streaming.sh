#!/bin/bash
# Script para limpiar el estado del streaming en Redis

echo "🧹 Limpiando estado del streaming en Redis..."

# Limpiar estado de streaming
redis-cli -p 6378 DEL streaming:state
redis-cli -p 6378 DEL streaming:stop_requested

echo "✅ Estado limpiado. Verifica:"
echo ""
redis-cli -p 6378 HGETALL streaming:state
echo ""
echo "Si no aparece nada, el estado fue limpiado correctamente."
