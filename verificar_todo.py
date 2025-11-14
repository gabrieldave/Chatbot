"""Verificar estado completo del sistema"""
import psutil
import sys
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 80)
print("🔍 VERIFICACIÓN COMPLETA DEL SISTEMA")
print("=" * 80)
print(f"Tiempo: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Buscar procesos
ingest_procs = []
monitor_procs = []

for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        if proc.info['name'] == 'python.exe' and proc.info['cmdline']:
            cmdline = ' '.join(proc.info['cmdline'])
            if 'ingest_parallel_tier3.py' in cmdline.lower():
                proc_obj = psutil.Process(proc.info['pid'])
                ingest_procs.append({
                    'pid': proc.info['pid'],
                    'mem': proc_obj.memory_info().rss / (1024**2),
                    'cpu': proc_obj.cpu_percent(interval=0.5)
                })
            elif 'monitor_y_ajustar_workers.py' in cmdline.lower():
                proc_obj = psutil.Process(proc.info['pid'])
                monitor_procs.append({
                    'pid': proc.info['pid'],
                    'mem': proc_obj.memory_info().rss / (1024**2),
                    'cpu': proc_obj.cpu_percent(interval=0.5)
                })
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        continue

print("📊 PROCESOS ACTIVOS:")
print()

if ingest_procs:
    print(f"✅ Proceso de ingestión: {len(ingest_procs)} proceso(s)")
    for p in ingest_procs:
        print(f"   PID: {p['pid']} | Mem: {p['mem']:.1f} MB | CPU: {p['cpu']:.1f}%")
else:
    print("⚠️  No hay proceso de ingestión corriendo")

print()

if monitor_procs:
    print(f"✅ Monitor inteligente: {len(monitor_procs)} proceso(s)")
    for p in monitor_procs:
        print(f"   PID: {p['pid']} | Mem: {p['mem']:.1f} MB | CPU: {p['cpu']:.1f}%")
else:
    print("⚠️  No hay monitor corriendo")

print()
print("=" * 80)



