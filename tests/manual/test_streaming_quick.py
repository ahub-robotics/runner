#!/usr/bin/env python3
"""
Script rápido para probar si el streaming funciona sin crashear Python
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
print("TEST RÁPIDO: ¿Python crashea al iniciar streaming?")
print("=" * 60)

# Login
print("\n[1] Autenticando...")
response = session.post(f"{BASE_URL}/login", data={"token": TOKEN}, verify=False, allow_redirects=False)
if response.status_code in [302, 200]:
    print("✅ Login exitoso")
else:
    print(f"❌ Login falló: {response.status_code}")
    exit(1)

# Iniciar streaming
print("\n[2] Iniciando streaming...")
try:
    response = session.post(f"{BASE_URL}/stream/start", verify=False, timeout=5)
    data = response.json()
    print(f"  Response: {data}")

    if data.get('success'):
        print("✅ Streaming iniciado sin crash")
        task_id = data.get('task_id')
        print(f"  Task ID: {task_id}")
    else:
        print(f"⚠️  Error: {data.get('message')}")
except Exception as e:
    print(f"❌ Excepción: {e}")
    exit(1)

# Esperar un momento
print("\n[3] Esperando 2 segundos...")
time.sleep(2)

# Verificar estado
print("\n[4] Verificando estado...")
try:
    response = session.get(f"{BASE_URL}/stream/status", verify=False, timeout=5)
    data = response.json()

    if data.get('active'):
        print("✅ Streaming está activo")
    else:
        print("⚠️  Streaming NO está activo")

    print(f"  Estado completo: {data}")
except Exception as e:
    print(f"❌ Error al verificar estado: {e}")

# Detener streaming
print("\n[5] Deteniendo streaming...")
try:
    response = session.post(f"{BASE_URL}/stream/stop", verify=False, timeout=5)
    data = response.json()

    if data.get('success'):
        print("✅ Streaming detenido")
    else:
        print(f"⚠️  Error: {data.get('message')}")
except Exception as e:
    print(f"❌ Error al detener: {e}")

print("\n" + "=" * 60)
print("TEST COMPLETADO - Python NO crasheó")
print("=" * 60)