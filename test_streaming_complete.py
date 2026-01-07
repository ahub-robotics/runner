#!/usr/bin/env python3
"""
Script para probar el streaming completo con autenticación
"""
import requests
import json
import time
import urllib3

# Deshabilitar advertencias SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuración
BASE_URL = "https://localhost:5001"
TOKEN = "eff7df3018dc2b2271165865c0f78aa17ce5df27"

print("=" * 60)
print("TEST DE STREAMING COMPLETO")
print("=" * 60)

# Crear sesión con cookies
session = requests.Session()

# Test 1: Login
print("\n[1/5] Probando login...")
try:
    response = session.post(
        f"{BASE_URL}/login",
        data={"token": TOKEN},
        verify=False,
        allow_redirects=False
    )
    if response.status_code in [302, 200]:
        print("✅ Login exitoso")
        print(f"   Cookies: {session.cookies.get_dict()}")
    else:
        print(f"❌ Login falló: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        exit(1)
except Exception as e:
    print(f"❌ Error en login: {e}")
    exit(1)

# Test 2: Verificar acceso a stream-view
print("\n[2/5] Verificando acceso a /stream-view...")
try:
    response = session.get(f"{BASE_URL}/stream-view", verify=False)
    if response.status_code == 200:
        print("✅ Acceso a /stream-view OK")
        if "Live Stream" in response.text:
            print("   Página de streaming cargada correctamente")
    else:
        print(f"❌ No se puede acceder: {response.status_code}")
        exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# Test 3: Iniciar streaming
print("\n[3/5] Iniciando streaming...")
try:
    response = session.post(f"{BASE_URL}/stream/start", verify=False)
    data = response.json()
    print(f"   Response: {data}")

    if data.get('success'):
        print("✅ Streaming iniciado correctamente")
        print(f"   Task ID: {data.get('task_id')}")
    else:
        print(f"⚠️  Respuesta: {data.get('message')}")
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# Test 4: Verificar estado
print("\n[4/5] Verificando estado del streaming...")
time.sleep(1)
try:
    response = session.get(f"{BASE_URL}/stream/status", verify=False)
    data = response.json()
    print(f"   Response: {data}")

    if data.get('success') and data.get('active'):
        print("✅ Streaming activo")
        print(f"   Clientes: {data.get('clients', 0)}")
    else:
        print(f"⚠️  Streaming no está activo: {data}")
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# Test 5: Probar feed (solo primeros bytes)
print("\n[5/5] Probando feed de video...")
try:
    response = session.get(
        f"{BASE_URL}/stream/feed",
        verify=False,
        stream=True,
        timeout=5
    )

    print(f"   Status: {response.status_code}")
    print(f"   Content-Type: {response.headers.get('Content-Type')}")

    if response.status_code == 200:
        # Leer primeros chunks
        chunks_received = 0
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                chunks_received += 1
                if chunks_received == 1:
                    print(f"   Primer chunk recibido ({len(chunk)} bytes)")
                if chunks_received >= 3:
                    print(f"✅ Feed funcionando - {chunks_received} chunks recibidos")
                    break

        if chunks_received == 0:
            print("⚠️  No se recibieron datos del feed")
    else:
        print(f"❌ Feed error: {response.status_code}")

except requests.exceptions.Timeout:
    print("⚠️  Timeout esperando datos del feed")
except Exception as e:
    print(f"❌ Error: {e}")

# Limpiar: detener streaming
print("\n[CLEANUP] Deteniendo streaming...")
try:
    response = session.post(f"{BASE_URL}/stream/stop", verify=False)
    data = response.json()
    if data.get('success'):
        print("✅ Streaming detenido")
except Exception as e:
    print(f"⚠️  Error deteniendo: {e}")

print("\n" + "=" * 60)
print("TESTS COMPLETADOS")
print("=" * 60)
print("\nPara acceder manualmente:")
print(f"  1. Ve a: {BASE_URL}/login")
print(f"  2. Ingresa el token: {TOKEN}")
print(f"  3. Luego ve a: {BASE_URL}/stream-view")
print(f"  4. Click en 'Iniciar' para ver el streaming")