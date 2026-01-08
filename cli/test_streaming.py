#!/usr/bin/env python3
"""
Test Streaming Diagnostics - Robot Runner

Script para diagnosticar problemas con el streaming.
"""
import sys
from pathlib import Path

# Asegurar que el directorio raíz está en el path
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))


def test_streaming():
    """Diagnóstico completo del sistema de streaming."""
    print("\n" + "="*70)
    print("  DIAGNÓSTICO DE STREAMING - ROBOT RUNNER")
    print("="*70 + "\n")

    errors = []
    warnings = []

    # 1. Verificar Redis
    print("📋 [1/6] Verificando Redis...")
    try:
        import redis
        client = redis.Redis(host='localhost', port=6378, socket_connect_timeout=2)
        client.ping()
        print("    ✅ Redis está disponible")

        # Verificar estado de streaming
        state = client.hgetall('streaming:state')
        if state:
            print(f"    📊 Estado actual en Redis:")
            for k, v in state.items():
                k_str = k.decode('utf-8') if isinstance(k, bytes) else k
                v_str = v.decode('utf-8') if isinstance(v, bytes) else v
                print(f"       - {k_str}: {v_str}")
        else:
            print("    ℹ️  No hay estado de streaming en Redis")
    except Exception as e:
        error_msg = f"Redis no disponible: {e}"
        errors.append(error_msg)
        print(f"    ❌ {error_msg}")

    # 2. Verificar Celery
    print("\n📋 [2/6] Verificando Celery...")
    try:
        from shared.celery_app.config import celery_app

        # Verificar workers activos
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()

        if active_workers:
            print(f"    ✅ Celery workers activos: {len(active_workers)}")
            for worker, tasks in active_workers.items():
                print(f"       - {worker}: {len(tasks)} tareas activas")
                for task in tasks:
                    print(f"         * {task.get('name', 'unknown')} (id: {task.get('id', 'N/A')[:8]}...)")
        else:
            warning_msg = "No hay workers de Celery activos"
            warnings.append(warning_msg)
            print(f"    ⚠️  {warning_msg}")

        # Verificar concurrencia
        stats = inspect.stats()
        if stats:
            for worker, info in stats.items():
                pool_settings = info.get('pool', {})
                max_concurrency = pool_settings.get('max-concurrency', 'unknown')
                print(f"    📊 Concurrencia configurada: {max_concurrency}")
                if max_concurrency == 1:
                    warning_msg = "Concurrencia es 1, streaming puede bloquearse si hay ejecución"
                    warnings.append(warning_msg)
                    print(f"    ⚠️  {warning_msg}")
    except Exception as e:
        error_msg = f"Error verificando Celery: {e}"
        errors.append(error_msg)
        print(f"    ❌ {error_msg}")

    # 3. Verificar imports de streaming
    print("\n📋 [3/6] Verificando imports de streaming...")
    try:
        from streaming.streamer import ScreenStreamer
        print("    ✅ ScreenStreamer importado correctamente")

        from streaming.tasks import start_streaming_task, stop_streaming_task
        print("    ✅ Tareas de streaming importadas correctamente")

        from api.streaming.control import streaming_control_bp
        print("    ✅ Blueprint de control importado correctamente")

        from api.streaming.feed import streaming_feed_bp
        print("    ✅ Blueprint de feed importado correctamente")
    except Exception as e:
        error_msg = f"Error en imports: {e}"
        errors.append(error_msg)
        print(f"    ❌ {error_msg}")
        import traceback
        traceback.print_exc()

    # 4. Verificar captura de pantalla
    print("\n📋 [4/6] Verificando captura de pantalla...")
    try:
        import mss
        with mss.mss() as sct:
            monitors = sct.monitors
            print(f"    ✅ Librería MSS disponible")
            print(f"    📊 Monitores detectados: {len(monitors) - 1}")  # -1 porque [0] es "all"
            for i, monitor in enumerate(monitors[1:], 1):
                print(f"       - Monitor {i}: {monitor['width']}x{monitor['height']}")
    except Exception as e:
        error_msg = f"Error con captura de pantalla: {e}"
        errors.append(error_msg)
        print(f"    ❌ {error_msg}")

    # 5. Verificar certificados SSL
    print("\n📋 [5/6] Verificando certificados SSL...")
    try:
        from shared.config.loader import get_resource_path
        import os

        cert_path = get_resource_path('ssl/cert.pem')
        key_path = get_resource_path('ssl/key.pem')

        if os.path.exists(cert_path):
            print(f"    ✅ Certificado encontrado: {cert_path}")
        else:
            warning_msg = f"Certificado no encontrado: {cert_path}"
            warnings.append(warning_msg)
            print(f"    ⚠️  {warning_msg}")

        if os.path.exists(key_path):
            print(f"    ✅ Clave privada encontrada: {key_path}")
        else:
            warning_msg = f"Clave privada no encontrada: {key_path}"
            warnings.append(warning_msg)
            print(f"    ⚠️  {warning_msg}")
    except Exception as e:
        warning_msg = f"Error verificando certificados: {e}"
        warnings.append(warning_msg)
        print(f"    ⚠️  {warning_msg}")

    # 6. Test de inicio de streaming
    print("\n📋 [6/6] Intentando iniciar streaming de prueba...")
    try:
        from streaming.tasks import start_streaming_task

        print("    ℹ️  Enviando tarea de inicio...")
        task = start_streaming_task.delay(
            host='0.0.0.0',
            port=8765,
            fps=10,
            quality=50,
            use_ssl=True
        )

        print(f"    ✅ Tarea enviada: {task.id}")
        print(f"    ⏳ Esperando 2 segundos...")

        import time
        time.sleep(2)

        # Verificar estado
        from celery.result import AsyncResult
        result = AsyncResult(task.id, app=celery_app)
        print(f"    📊 Estado de la tarea: {result.state}")

        if result.state == 'STARTED':
            print(f"    ✅ Tarea iniciada correctamente")

            # Verificar Redis
            state = client.hgetall('streaming:state')
            if state and state.get(b'active') == b'true':
                print(f"    ✅ Estado marcado como activo en Redis")
            else:
                warning_msg = "Tarea iniciada pero estado no activo en Redis"
                warnings.append(warning_msg)
                print(f"    ⚠️  {warning_msg}")

            # Detener streaming de prueba
            print(f"    🛑 Deteniendo streaming de prueba...")
            from streaming.tasks import stop_streaming_task
            stop_streaming_task.delay()
            time.sleep(1)
        else:
            warning_msg = f"Tarea en estado inesperado: {result.state}"
            warnings.append(warning_msg)
            print(f"    ⚠️  {warning_msg}")

    except Exception as e:
        error_msg = f"Error en test de streaming: {e}"
        errors.append(error_msg)
        print(f"    ❌ {error_msg}")
        import traceback
        traceback.print_exc()

    # Resumen
    print("\n" + "="*70)
    print("  RESUMEN")
    print("="*70)

    if not errors and not warnings:
        print("\n✅ TODO CORRECTO - El streaming debería funcionar")
    else:
        if errors:
            print(f"\n❌ ERRORES CRÍTICOS ({len(errors)}):")
            for i, error in enumerate(errors, 1):
                print(f"   {i}. {error}")

        if warnings:
            print(f"\n⚠️  ADVERTENCIAS ({len(warnings)}):")
            for i, warning in enumerate(warnings, 1):
                print(f"   {i}. {warning}")

    print("\n" + "="*70)
    print()

    return len(errors) == 0


if __name__ == '__main__':
    try:
        success = test_streaming()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
