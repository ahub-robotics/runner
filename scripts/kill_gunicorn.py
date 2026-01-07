#!/usr/bin/env python3
"""
================================================================================
Kill Gunicorn V2 - Script mejorado para detener procesos de Gunicorn
================================================================================

Versión mejorada con mejor manejo de timeouts y señales.

Uso:
    python scripts/kill_gunicorn_v2.py
    ./scripts/kill_gunicorn_v2.py

================================================================================
"""

import os
import sys
import time
import signal
import subprocess
import platform
from pathlib import Path


def find_gunicorn_processes():
    """
    Encuentra todos los procesos de Gunicorn corriendo.

    Returns:
        list: Lista de PIDs de procesos de Gunicorn
    """
    pids = set()

    try:
        if platform.system() == 'Windows':
            # En Windows, buscar procesos python
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FO', 'CSV'],
                capture_output=True,
                text=True,
                timeout=10
            )
            for line in result.stdout.split('\n'):
                if 'python' in line.lower():
                    parts = line.split(',')
                    if len(parts) >= 2:
                        pid_str = parts[1].strip('"')
                        try:
                            pids.add(int(pid_str))
                        except ValueError:
                            pass
        else:
            # En Linux/macOS, buscar procesos relacionados con gunicorn o run.py --server-only
            # Método 1: Buscar directamente "gunicorn"
            try:
                result = subprocess.run(
                    ['pgrep', '-f', 'gunicorn'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                for pid_str in result.stdout.strip().split('\n'):
                    if pid_str:
                        try:
                            pids.add(int(pid_str))
                        except ValueError:
                            pass
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

            # Método 2: Buscar "run.py --server-only" o "src.app --server-only"
            for pattern in ['run.py.*--server-only', 'src.app.*--server-only']:
                try:
                    result = subprocess.run(
                        ['pgrep', '-f', pattern],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    for pid_str in result.stdout.strip().split('\n'):
                        if pid_str:
                            try:
                                pids.add(int(pid_str))
                            except ValueError:
                                pass
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass

            # Método 3: Buscar procesos escuchando en puertos comunes (5001, 5055)
            for port in [5001, 5055]:
                try:
                    result = subprocess.run(
                        ['lsof', '-t', '-i', f':{port}', '-sTCP:LISTEN'],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    for pid_str in result.stdout.strip().split('\n'):
                        if pid_str:
                            try:
                                pids.add(int(pid_str))
                            except ValueError:
                                pass
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass

            # Método 4 (fallback): Usar ps aux y buscar manualmente
            if not pids:
                try:
                    result = subprocess.run(
                        ['ps', 'aux'],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )

                    for line in result.stdout.split('\n'):
                        if (('gunicorn' in line or 'run.py' in line or 'src.app' in line)
                            and '--server-only' in line
                            and 'grep' not in line):
                            parts = line.split()
                            if len(parts) >= 2:
                                try:
                                    pids.add(int(parts[1]))
                                except (ValueError, IndexError):
                                    pass
                except Exception:
                    pass

    except subprocess.TimeoutExpired:
        print(f"⚠️  Timeout buscando procesos")
    except Exception as e:
        print(f"⚠️  Error buscando procesos: {e}")

    return list(pids)


def kill_process(pid, force=False):
    """
    Mata un proceso de forma simple y directa.

    Args:
        pid (int): PID del proceso a matar
        force (bool): Si True, usa SIGKILL en lugar de SIGTERM

    Returns:
        bool: True si el proceso fue terminado, False si no
    """
    try:
        if platform.system() == 'Windows':
            # En Windows, usar taskkill
            cmd = ['taskkill', '/PID', str(pid)]
            if force:
                cmd.insert(1, '/F')
            subprocess.run(cmd, capture_output=True, timeout=5)
        else:
            # En Linux/macOS, usar kill directo
            sig = signal.SIGKILL if force else signal.SIGTERM
            os.kill(pid, sig)

        return True

    except (ProcessLookupError, PermissionError):
        # Proceso ya no existe o no tenemos permisos
        return True
    except subprocess.TimeoutExpired:
        print(f"   ⚠️  Timeout matando PID {pid}")
        return False
    except Exception as e:
        print(f"   ⚠️  Error con PID {pid}: {e}")
        return False


def main():
    """Función principal."""
    print("=" * 70)
    print("  Deteniendo procesos de Gunicorn (v2)")
    print("=" * 70)
    print()

    # Buscar procesos de Gunicorn
    pids = find_gunicorn_processes()

    if not pids:
        print("✅ No hay procesos de Gunicorn corriendo")
        return 0

    print(f"📋 Procesos de Gunicorn encontrados: {len(pids)}")
    print(f"   PIDs: {', '.join(map(str, pids))}")
    print()

    # Intentar terminación grácil primero (SIGTERM)
    print("⚠️  Intentando terminación grácil (SIGTERM)...")
    for pid in pids:
        print(f"   Deteniendo PID {pid}...", end=' ')
        if kill_process(pid, force=False):
            print("✓")
        else:
            print("✗")

    # Esperar un poco
    print("⏳ Esperando...")
    for i in range(3):
        time.sleep(1)
        print(".", end='', flush=True)
    print()

    # Verificar si quedaron procesos
    remaining_pids = find_gunicorn_processes()

    if not remaining_pids:
        print("✅ Todos los procesos han sido detenidos")
        return 0

    # Si quedan procesos, forzar terminación (SIGKILL)
    print()
    print("⚠️  Forzando terminación (SIGKILL)...")
    for pid in remaining_pids:
        print(f"   Forzando PID {pid}...", end=' ')
        if kill_process(pid, force=True):
            print("✓")
        else:
            print("✗")

    # Esperar un poco
    time.sleep(1)

    # Verificación final
    final_check = find_gunicorn_processes()

    if not final_check:
        print("✅ Todos los procesos han sido detenidos (forzado)")
        return 0
    else:
        print("❌ Algunos procesos no pudieron ser detenidos:")
        print(f"   PIDs restantes: {', '.join(map(str, final_check))}")
        return 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)