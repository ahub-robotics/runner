#!/usr/bin/env python3
"""
Script de diagnóstico para identificar problemas en la captura de pantalla.
"""
import sys
import io

print("=" * 60)
print("DIAGNÓSTICO DE CAPTURA DE PANTALLA")
print("=" * 60)

# Test 1: Verificar mss
print("\n[1/5] Verificando biblioteca mss...")
try:
    import mss
    print("✅ mss importado correctamente")
    print(f"   Versión: {mss.__version__ if hasattr(mss, '__version__') else 'desconocida'}")
except Exception as e:
    print(f"❌ Error importando mss: {e}")
    sys.exit(1)

# Test 2: Verificar PIL/Pillow
print("\n[2/5] Verificando PIL/Pillow...")
try:
    from PIL import Image, ImageDraw
    print("✅ PIL importado correctamente")
    print(f"   Versión Pillow: {Image.__version__ if hasattr(Image, '__version__') else 'desconocida'}")

    # Verificar si LANCZOS existe
    if hasattr(Image, 'LANCZOS'):
        print("   ⚠️  Image.LANCZOS existe (deprecado)")
    if hasattr(Image, 'Resampling'):
        print("   ✅ Image.Resampling existe (nuevo método)")
        print(f"      - LANCZOS disponible: {hasattr(Image.Resampling, 'LANCZOS')}")
except Exception as e:
    print(f"❌ Error importando PIL: {e}")
    sys.exit(1)

# Test 3: Verificar que hay monitores disponibles
print("\n[3/5] Verificando monitores disponibles...")
try:
    with mss.mss() as sct:
        monitors = sct.monitors
        print(f"✅ {len(monitors)} monitor(es) detectado(s)")
        for i, monitor in enumerate(monitors):
            print(f"   Monitor {i}: {monitor}")

        if len(monitors) < 2:  # monitors[0] es el virtual que combina todos
            print("   ⚠️  Advertencia: Pocos monitores detectados")
except Exception as e:
    print(f"❌ Error detectando monitores: {e}")
    sys.exit(1)

# Test 4: Intentar captura de pantalla
print("\n[4/5] Intentando captura de pantalla...")
try:
    with mss.mss() as sct:
        monitor = sct.monitors[0]
        print(f"   Capturando monitor: {monitor}")
        screenshot = sct.grab(monitor)
        print(f"✅ Captura exitosa: {screenshot.size}")

        # Convertir a PIL Image
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        print(f"✅ Conversión a PIL Image exitosa: {img.size}")

except Exception as e:
    print(f"❌ Error en captura: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Probar resize con el método correcto
print("\n[5/5] Probando resize de imagen...")
try:
    # Determinar el método correcto para LANCZOS
    if hasattr(Image, 'Resampling') and hasattr(Image.Resampling, 'LANCZOS'):
        lanczos_filter = Image.Resampling.LANCZOS
        print("   Usando Image.Resampling.LANCZOS (nuevo)")
    elif hasattr(Image, 'LANCZOS'):
        lanczos_filter = Image.LANCZOS
        print("   Usando Image.LANCZOS (deprecado)")
    else:
        print("   ❌ No se encontró LANCZOS, usando BICUBIC")
        lanczos_filter = Image.BICUBIC if hasattr(Image, 'BICUBIC') else 3

    max_width = 1280
    if img.width > max_width:
        ratio = max_width / img.width
        new_size = (max_width, int(img.height * ratio))
        img_resized = img.resize(new_size, lanczos_filter)
        print(f"✅ Resize exitoso: {img.size} → {img_resized.size}")
    else:
        img_resized = img
        print(f"   Imagen ya es pequeña: {img.size}")

    # Probar conversión a JPEG
    buffer = io.BytesIO()
    img_resized.save(buffer, format="JPEG", quality=75, optimize=True)
    jpeg_size = len(buffer.getvalue())
    print(f"✅ Conversión a JPEG exitosa: {jpeg_size} bytes")

except Exception as e:
    print(f"❌ Error en resize/JPEG: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ TODOS LOS TESTS PASARON CORRECTAMENTE")
print("=" * 60)
print("\nLa captura de pantalla debería funcionar.")
print("Si aún así falla el streaming, el problema está en:")
print("  - Configuración de Redis")
print("  - Conexión SSE desde el navegador")
print("  - Permisos de pantalla en macOS")
