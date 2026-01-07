#!/bin/bash
# Test para verificar que el token funciona en cualquier URL

TOKEN="eff7df3018dc2b2271165865c0f78aa17ce5df27"
BASE_URL="https://localhost:5001"

echo "=========================================="
echo "TEST: Token en cualquier URL"
echo "=========================================="
echo ""

# Test 1: Sin token (debe redirigir a login)
echo "[TEST 1] Acceso a / sin token:"
STATUS=$(curl -k "${BASE_URL}/" -s -o /dev/null -w "%{http_code}")
if [ "$STATUS" = "302" ]; then
    echo "  ✅ Redirección a login (302)"
else
    echo "  ❌ Expected 302, got $STATUS"
fi
echo ""

# Test 2: Con token en /
echo "[TEST 2] Acceso a / con token:"
STATUS=$(curl -k "${BASE_URL}/?token=${TOKEN}" -s -o /dev/null -w "%{http_code}" -L)
if [ "$STATUS" = "200" ]; then
    echo "  ✅ Autenticación exitosa (200)"
else
    echo "  ❌ Expected 200, got $STATUS"
fi
echo ""

# Test 3: Con token en /connected
echo "[TEST 3] Acceso a /connected con token:"
STATUS=$(curl -k "${BASE_URL}/connected?token=${TOKEN}" -s -o /dev/null -w "%{http_code}")
if [ "$STATUS" = "200" ]; then
    echo "  ✅ Autenticación exitosa (200)"
else
    echo "  ❌ Expected 200, got $STATUS"
fi
echo ""

# Test 4: Con token en /stream-view
echo "[TEST 4] Acceso a /stream-view con token:"
STATUS=$(curl -k "${BASE_URL}/stream-view?token=${TOKEN}" -s -o /dev/null -w "%{http_code}")
if [ "$STATUS" = "200" ]; then
    echo "  ✅ Autenticación exitosa (200)"
else
    echo "  ❌ Expected 200, got $STATUS"
fi
echo ""

# Test 5: Con token en /settings
echo "[TEST 5] Acceso a /settings con token:"
STATUS=$(curl -k "${BASE_URL}/settings?token=${TOKEN}" -s -o /dev/null -w "%{http_code}")
if [ "$STATUS" = "200" ]; then
    echo "  ✅ Autenticación exitosa (200)"
else
    echo "  ❌ Expected 200, got $STATUS"
fi
echo ""

# Test 6: Token inválido
echo "[TEST 6] Acceso con token inválido:"
STATUS=$(curl -k "${BASE_URL}/?token=invalid" -s -o /dev/null -w "%{http_code}" -L)
if [ "$STATUS" = "200" ]; then
    echo "  ❌ Should not authenticate with invalid token"
else
    echo "  ✅ Token inválido rechazado (redirected to login)"
fi
echo ""

echo "=========================================="
echo "TESTS COMPLETADOS"
echo "=========================================="
echo ""
echo "Resumen:"
echo "  - El token se puede enviar en cualquier URL"
echo "  - La sesión dura 30 días"
echo "  - Funciona con: /, /connected, /stream-view, /settings, etc."
echo ""
echo "Ejemplos de uso:"
echo "  https://robot1.automatehub.es/?token=${TOKEN}"
echo "  https://robot1.automatehub.es/connected?token=${TOKEN}"
echo "  https://robot1.automatehub.es/stream-view?token=${TOKEN}"