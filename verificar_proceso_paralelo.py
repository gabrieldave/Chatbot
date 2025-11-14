"""Verificar si el proceso paralelo está corriendo"""
import psutil
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

print("🔍 Buscando procesos de ingestión paralela...")
print()

found = False
for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        if proc.info['name'] == 'python.exe' and proc.info['cmdline']:
            cmdline = ' '.join(proc.info['cmdline'])
            if 'ingest_parallel_tier3.py' in cmdline.lower():
                found = True
                proc_obj = psutil.Process(proc.info['pid'])
                print(f"✅ Proceso encontrado:")
                print(f"   PID: {proc.info['pid']}")
                print(f"   Memoria: {proc_obj.memory_info().rss / (1024**2):.1f} MB")
                print(f"   CPU: {proc_obj.cpu_percent(interval=0.5):.1f}%")
                print(f"   Estado: {proc_obj.status()}")
                print()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        continue

if not found:
    print("⚠️  No se encontró proceso de ingestión paralela corriendo")
    print("   Ejecuta: python ingest_parallel_tier3.py")



