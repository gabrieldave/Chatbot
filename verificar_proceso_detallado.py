"""
🔍 VERIFICACIÓN DETALLADA DEL PROCESO
======================================

Verifica si el proceso está realmente trabajando o está bloqueado
"""

import os
import sys
import time
import psutil
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 80)
print("🔍 VERIFICACIÓN DETALLADA DEL PROCESO")
print("=" * 80)

# Buscar proceso de ingest
ingest_proc = None
for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 'memory_info', 'status']):
    try:
        if proc.info['name'] == 'python.exe' and proc.info['cmdline']:
            cmdline = ' '.join(proc.info['cmdline'])
            if 'ingest_improved.py' in cmdline.lower():
                ingest_proc = proc
                break
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        continue

if not ingest_proc:
    print("❌ No se encontró proceso de ingest corriendo")
    sys.exit(1)

# Obtener información detallada
try:
    pid = ingest_proc.pid
    status = ingest_proc.status()
    memory_info = ingest_proc.memory_info()
    memory_mb = memory_info.rss / (1024 * 1024)
    cpu_percent = ingest_proc.cpu_percent(interval=1)
    create_time = ingest_proc.create_time()
    uptime = time.time() - create_time
    
    # Obtener threads
    num_threads = ingest_proc.num_threads()
    
    # Obtener conexiones de red (para ver si está esperando API)
    try:
        connections = ingest_proc.connections()
        num_connections = len(connections)
    except:
        num_connections = "N/A"
    
    print(f"\n📊 INFORMACIÓN DEL PROCESO:")
    print(f"   PID: {pid}")
    print(f"   Estado: {status}")
    print(f"   CPU: {cpu_percent:.1f}%")
    print(f"   RAM: {memory_mb:.1f} MB")
    print(f"   Threads: {num_threads}")
    print(f"   Conexiones de red: {num_connections}")
    print(f"   Tiempo activo: {int(uptime//60)}m {int(uptime%60)}s")
    
    print(f"\n🔍 ANÁLISIS:")
    
    # Análisis de estado
    if status == 'running':
        print(f"   ✅ Proceso está corriendo")
    elif status == 'sleeping':
        print(f"   ⚠️  Proceso está en estado 'sleeping' (puede estar esperando I/O)")
    else:
        print(f"   ⚠️  Proceso en estado: {status}")
    
    # Análisis de CPU
    if cpu_percent > 80:
        print(f"   ✅ CPU alto ({cpu_percent:.1f}%) - Está procesando activamente")
    elif cpu_percent > 20:
        print(f"   ⚠️  CPU moderado ({cpu_percent:.1f}%) - Puede estar esperando algo")
    else:
        print(f"   ⚠️  CPU bajo ({cpu_percent:.1f}%) - Puede estar bloqueado o esperando")
    
    # Análisis de memoria
    if memory_mb > 800:
        print(f"   ✅ RAM alta ({memory_mb:.1f} MB) - Probablemente cargó un batch grande")
        print(f"      Con batch_size=150, esto es normal")
    elif memory_mb > 400:
        print(f"   ⚠️  RAM moderada ({memory_mb:.1f} MB) - Puede estar procesando")
    else:
        print(f"   ⚠️  RAM baja ({memory_mb:.1f} MB) - Puede no estar cargando batches")
    
    # Análisis de threads
    if num_threads > 5:
        print(f"   ✅ Múltiples threads ({num_threads}) - Está trabajando en paralelo")
    else:
        print(f"   ⚠️  Pocos threads ({num_threads}) - Puede estar procesando secuencialmente")
    
    # Análisis de tiempo
    if uptime > 600:  # Más de 10 minutos
        print(f"   ⚠️  Proceso lleva {int(uptime//60)} minutos corriendo")
        print(f"      Si no hay progreso, puede estar bloqueado")
    
    print(f"\n" + "=" * 80)
    print("💡 DIAGNÓSTICO")
    print("=" * 80)
    
    # Diagnóstico
    if cpu_percent > 80 and memory_mb > 800:
        print(f"\n✅ ESCENARIO MÁS PROBABLE:")
        print(f"   El proceso está procesando un batch grande (150 archivos)")
        print(f"   Esto puede tomar varios minutos, especialmente si:")
        print(f"   • Hay archivos PDF grandes")
        print(f"   • Está generando embeddings (llamadas a OpenAI)")
        print(f"   • Está insertando muchos chunks a Supabase")
        print(f"\n💡 RECOMENDACIÓN:")
        print(f"   Espera 5-10 minutos más")
        print(f"   Con batch_size=150, cada batch puede tomar 5-15 minutos")
        print(f"   Es normal que no veas progreso inmediato")
        
    elif cpu_percent < 20:
        print(f"\n⚠️  ESCENARIO PREOCUPANTE:")
        print(f"   El proceso tiene CPU bajo ({cpu_percent:.1f}%)")
        print(f"   Puede estar:")
        print(f"   • Esperando respuesta de API de OpenAI (embeddings)")
        print(f"   • Esperando I/O de disco")
        print(f"   • Bloqueado por algún error silencioso")
        print(f"\n💡 RECOMENDACIÓN:")
        print(f"   Verifica los logs del proceso")
        print(f"   Puede estar esperando la API de OpenAI")
        print(f"   Si pasa más de 15 minutos sin progreso, reinicia")
        
    else:
        print(f"\n⚠️  ESCENARIO INTERMEDIO:")
        print(f"   El proceso está activo pero no tan intenso")
        print(f"   Puede estar procesando pero lentamente")
        print(f"\n💡 RECOMENDACIÓN:")
        print(f"   Monitorea por 5-10 minutos más")
        print(f"   Si no hay progreso, puede haber un problema")
    
    print(f"\n📋 PRÓXIMOS PASOS:")
    print(f"   1. Espera 5-10 minutos más")
    print(f"   2. Verifica el progreso: python check_progress_now.py")
    print(f"   3. Si no hay progreso después de 15 minutos, reinicia el proceso")
    print(f"   4. Considera reducir batch_size a 100 si el problema persiste")
    
except Exception as e:
    print(f"❌ Error obteniendo información: {e}")

print("\n" + "=" * 80)




