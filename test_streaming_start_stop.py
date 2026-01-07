#!/usr/bin/env python3
"""
Script para probar el ciclo start/stop del streaming
"""
import requests
import time
import urllib3

# Deshabilitar advertencias SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://localhost:5001"
TOKEN = "eff7df3018dc2b2271165865c0f78aa17ce5df27"

# Crear sesión con cookies
session = requests.Session()

print("=" * 60)
print("TEST: CICLO START/STOP DEL STREAMING")
print("=" * 60)

# Login
print("\n[LOGIN] Autenticando...")
response = session.post(f"{BASE_URL}/login", data={"token": TOKEN}, verify=False, allow_redirects=False)
if response.status_code in [302, 200]:
    print("✅ Login exitoso")
else:
    print(f"❌ Login falló: {response.status_code}")
    exit(1)

# Test 1: Iniciar streaming
print("\n[TEST 1] Iniciando streaming...")
response = session.post(f"{BASE_URL}/stream/start", verify=False)
data = response.json()
print(f"  Response: {data}")

if data.get('success'):
    print("✅ Streaming iniciado")
    task_id_1 = data.get('task_id')
    print(f"  Task ID: {task_id_1}")
else:
    print(f"❌ Error: {data.get('message')}")
    exit(1)

# Esperar 2 segundos
print("\n⏳ Esperando 2 segundos...")
time.sleep(2)

# Test 2: Verificar estado
print("\n[TEST 2] Verificando estado...")
response = session.get(f"{BASE_URL}/stream/status", verify=False)
data = response.json()
print(f"  Response: {data}")

if data.get('active'):
    print("✅ Streaming está activo")
else:
    print("❌ Streaming NO está activo (debería estarlo)")

# Test 3: Detener streaming
print("\n[TEST 3] Deteniendo streaming...")
response = session.post(f"{BASE_URL}/stream/stop", verify=False)
data = response.json()
print(f"  Response: {data}")

if data.get('success'):
    print("✅ Señal de detención enviada")
else:
    print(f"⚠️  Error: {data.get('message')}")

# Esperar a que la tarea procese la detención
print("\n⏳ Esperando 3 segundos para que se procese la detención...")
time.sleep(3)

# Test 4: Verificar que se detuvo
print("\n[TEST 4] Verificando que se detuvo...")
response = session.get(f"{BASE_URL}/stream/status", verify=False)
data = response.json()
print(f"  Response: {data}")

if not data.get('active'):
    print("✅ Streaming está detenido correctamente")
else:
    print("❌ Streaming sigue activo (debería estar detenido)")
    print("   Esto significa que el worker de Celery no procesó la señal de stop")

# Test 5: Reiniciar streaming
print("\n[TEST 5] Reiniciando streaming...")
response = session.post(f"{BASE_URL}/stream/start", verify=False)
data = response.json()
print(f"  Response: {data}")

if data.get('success'):
    print("✅ Streaming reiniciado exitosamente")
    task_id_2 = data.get('task_id')
    print(f"  Task ID: {task_id_2}")
    if task_id_1 != task_id_2:
        print(f"  ✅ Nuevo task ID (correcto)")
else:
    print(f"❌ Error al reiniciar: {data.get('message')}")
    if "ya está activo" in data.get('message', '').lower():
        print("   ⚠️  El estado no se limpió correctamente")

# Esperar 2 segundos
print("\n⏳ Esperando 2 segundos...")
time.sleep(2)

# Test 6: Verificar estado final
print("\n[TEST 6] Verificando estado final...")
response = session.get(f"{BASE_URL}/stream/status", verify=False)
data = response.json()
print(f"  Response: {data}")

if data.get('active'):
    print("✅ Streaming está activo")
else:
    print("❌ Streaming NO está activo")

# Cleanup: Detener streaming
print("\n[CLEANUP] Deteniendo streaming...")
response = session.post(f"{BASE_URL}/stream/stop", verify=False)
data = response.json()
if data.get('success'):
    print("✅ Streaming detenido")

print("\n" + "=" * 60)
print("TESTS COMPLETADOS")
print("=" * 60)