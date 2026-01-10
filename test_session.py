#!/usr/bin/env python3
"""
Test de sesiones de Flask en Windows
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

def test_session():
    print("="*70)
    print("  🧪 TEST DE SESIONES FLASK")
    print("="*70)
    print()

    # 1. Crear app
    print("1. Creando Flask app...")
    from api.app import create_app
    app = create_app()
    print(f"   ✅ App creada")
    print(f"   Secret Key: {app.secret_key[:20]}...")
    print(f"   Session Cookie Name: {app.config.get('SESSION_COOKIE_NAME')}")
    print(f"   Permanent Session Lifetime: {app.config.get('PERMANENT_SESSION_LIFETIME')}")
    print()

    # 2. Test de sesión
    print("2. Test de sesión...")
    with app.test_client() as client:
        # Simular login
        print("   → POST /login con token")

        from shared.config.loader import get_config_data
        config = get_config_data()
        token = config.get('token')

        response = client.post('/login', data={'token': token}, follow_redirects=False)

        print(f"   ✅ Status: {response.status_code}")
        print(f"   ✅ Location: {response.headers.get('Location', 'N/A')}")

        # Verificar cookies
        cookies = response.headers.getlist('Set-Cookie')
        if cookies:
            print(f"   ✅ Cookies: {len(cookies)} cookie(s) enviada(s)")
            for cookie in cookies:
                print(f"      - {cookie[:80]}...")
        else:
            print(f"   ⚠️  No cookies en la respuesta")
        print()

        # Seguir redirección manualmente
        if response.status_code in [301, 302, 303, 307, 308]:
            location = response.headers.get('Location')
            print(f"3. Siguiendo redirección a: {location}")
            response2 = client.get(location)
            print(f"   ✅ Status: {response2.status_code}")

            if response2.status_code == 200:
                print(f"   ✅ Página cargada correctamente")
                # Verificar si hay contenido HTML
                if b'<html' in response2.data or b'<!DOCTYPE' in response2.data:
                    print(f"   ✅ HTML válido detectado")
                else:
                    print(f"   ⚠️  Respuesta no parece HTML")
                    print(f"   Contenido: {response2.data[:100]}...")
            else:
                print(f"   ❌ Error en página destino")
        else:
            print(f"   ❌ No se produjo redirección (esperado 302, recibido {response.status_code})")

    print()
    print("="*70)
    print("  ✅ TEST COMPLETADO")
    print("="*70)

if __name__ == '__main__':
    test_session()
