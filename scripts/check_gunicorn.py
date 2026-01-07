#!/usr/bin/env python3
"""
================================================================================
Check Gunicorn - Script para verificar el estado de Gunicorn
================================================================================

Descripción:
    Verifica si hay procesos de Gunicorn corriendo y muestra información
    detallada sobre ellos.

Uso:
    python scripts/check_gunicorn.py
    ./scripts/check_gunicorn.py

Códigos de salida:
    0 - No hay procesos corriendo
    1 - Hay procesos corriendo

Compatibilidad:
    - Linux/macOS: Usa ps y lsof
    - Windows: Usa tasklist y netstat

================================================================================
"""

import os
import sys
import subprocess
import platform


def find_gunicorn_processes():
    """
    Encuentra todos los procesos de Gunicorn corriendo con información detallada.

    Returns:
        list: Lista de diccionarios con información de cada proceso
    """
    processes = []
    current_pid = os.getpid()

    try:
        if platform.system() == 'Windows':
            # En Windows, buscar procesos python
            result = subprocess.run(
                ['tasklist', '/V', '/FI', 'IMAGENAME eq python.exe'],
                capture_output=True,
                text=True
            )

            for line in result.stdout.split('\n')[3:]:  # Skip headers
                if line.strip() and 'python' in line.lower():
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            processes.append({
                                'pid': parts[1],
                                'memory': parts[4],
                                'status': parts[6] if len(parts) > 6 else 'N/A'
                            })
                        except (IndexError, ValueError):
                            pass

        else:
            # En Linux/macOS, usar pgrep primero (más eficiente)
            try:
                result = subprocess.run(
                    ['pgrep', '-f', 'python.*gunicorn'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                pids = []
                for pid_str in result.stdout.strip().split('\n'):
                    if pid_str:
                        try:
                            pid = int(pid_str)
                            # Excluir el proceso actual y procesos de check/kill
                            if pid != current_pid:
                                pids.append(pid)
                        except ValueError:
                            pass

                # Obtener detalles de cada PID
                if pids:
                    result = subprocess.run(
                        ['ps', '-p', ','.join(map(str, pids)), '-o', 'user,pid,%cpu,%mem,time,command'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )

                    for line in result.stdout.split('\n')[1:]:  # Skip header
                        if line.strip():
                            parts = line.split(None, 5)
                            if len(parts) >= 6 and 'check_gunicorn' not in parts[5] and 'kill_gunicorn' not in parts[5]:
                                try:
                                    processes.append({
                                        'user': parts[0],
                                        'pid': parts[1],
                                        'cpu': parts[2],
                                        'mem': parts[3],
                                        'time': parts[4],
                                        'command': parts[5]
                                    })
                                except (IndexError, ValueError):
                                    pass

            except (subprocess.TimeoutExpired, FileNotFoundError):
                # Fallback a ps aux
                result = subprocess.run(
                    ['ps', 'aux'],
                    capture_output=True,
                    text=True
                )

                for line in result.stdout.split('\n'):
                    if 'gunicorn' in line and 'grep' not in line and 'check_gunicorn' not in line and 'kill_gunicorn' not in line:
                        parts = line.split()
                        if len(parts) >= 11:
                            pid = int(parts[1])
                            if pid != current_pid:
                                try:
                                    processes.append({
                                        'user': parts[0],
                                        'pid': parts[1],
                                        'cpu': parts[2],
                                        'mem': parts[3],
                                        'time': parts[9],
                                        'command': ' '.join(parts[10:])
                                    })
                                except (IndexError, ValueError):
                                    pass

    except Exception as e:
        print(f"⚠️  Error buscando procesos: {e}")

    return processes


def get_process_ports(pid):
    """
    Obtiene los puertos en uso por un proceso específico.

    Args:
        pid (str): PID del proceso

    Returns:
        list: Lista de puertos en uso
    """
    ports = []

    try:
        if platform.system() == 'Windows':
            result = subprocess.run(
                ['netstat', '-ano'],
                capture_output=True,
                text=True
            )

            for line in result.stdout.split('\n'):
                if pid in line and 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        addr = parts[1]
                        if ':' in addr:
                            port = addr.split(':')[-1]
                            ports.append(port)

        else:
            # En Linux/macOS, usar lsof
            result = subprocess.run(
                ['lsof', '-p', pid, '-P', '-n'],
                capture_output=True,
                text=True
            )

            for line in result.stdout.split('\n'):
                if 'LISTEN' in line:
                    parts = line.split()
                    if len(parts) >= 9:
                        addr = parts[8]
                        if ':' in addr:
                            port = addr.split(':')[-1]
                            ports.append(port)

    except Exception:
        pass

    return ports


def main():
    """Función principal."""
    print("=" * 70)
    print("  Estado de Gunicorn")
    print("=" * 70)
    print()

    # Buscar procesos de Gunicorn
    processes = find_gunicorn_processes()

    if not processes:
        print("✅ No hay procesos de Gunicorn corriendo")
        print()
        print("Para iniciar el servidor:")
        print("   python run.py")
        print("   python run.py --server-only  # Sin GUI")
        return 0

    print(f"🔍 Procesos de Gunicorn encontrados: {len(processes)}")
    print()

    # Mostrar información detallada
    print("📋 Detalles de los procesos:")
    print("-" * 70)

    if platform.system() == 'Windows':
        print(f"{'PID':<10} {'MEMORY':<15} {'STATUS':<20}")
        print("-" * 70)
        for proc in processes:
            print(f"{proc['pid']:<10} {proc['memory']:<15} {proc['status']:<20}")
    else:
        print(f"{'PID':<10} {'CPU%':<8} {'MEM%':<8} {'TIME':<12} {'COMMAND':<30}")
        print("-" * 70)
        for proc in processes:
            command = proc['command'][:30] + '...' if len(proc['command']) > 30 else proc['command']
            print(f"{proc['pid']:<10} {proc['cpu']:<8} {proc['mem']:<8} {proc['time']:<12} {command:<30}")

    print()

    # Mostrar PIDs
    pids = [proc['pid'] for proc in processes]
    print(f"PIDs: {', '.join(pids)}")
    print()

    # Verificar puertos en uso
    print("🔌 Puertos en uso:")
    for proc in processes:
        ports = get_process_ports(proc['pid'])
        if ports:
            print(f"   PID {proc['pid']}: {', '.join(ports)}")
        else:
            print(f"   PID {proc['pid']}: No se pudieron determinar puertos")
    print()

    # Sugerencias
    print("💡 Para detener los procesos:")
    print("   python scripts/kill_gunicorn.py")
    print("   ./scripts/kill_gunicorn.sh")
    print(f"   # O manualmente: kill -TERM {' '.join(pids)}")

    return 1


if __name__ == '__main__':
    sys.exit(main())