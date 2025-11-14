"""
🔍 VERIFICACIÓN DETALLADA DE OPENAI
===================================

Verifica si hay rate limiting o problemas con OpenAI
"""

import os
import sys
import time
import psutil
import subprocess
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 80)
print("🔍 VERIFICACIÓN DETALLADA DE OPENAI")
print("=" * 80)

# 1. Verificar proceso
print("\n1️⃣  ESTADO DEL PROCESO:")
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

if ingest_proc:
    cpu = ingest_proc.cpu_percent(interval=2)
    mem_mb = ingest_proc.memory_info().rss / (1024 * 1024)
    uptime = time.time() - ingest_proc.create_time()
    status = ingest_proc.status()
    
    print(f"   PID: {ingest_proc.pid}")
    print(f"   Estado: {status}")
    print(f"   CPU: {cpu:.1f}%")
    print(f"   RAM: {mem_mb:.1f} MB")
    print(f"   Tiempo: {int(uptime//60)}m {int(uptime%60)}s")
    
    if cpu < 5 and status == 'running':
        print(f"   ⚠️  CPU muy bajo - Puede estar bloqueado o esperando")
    elif cpu > 50:
        print(f"   ✅ CPU activo - Está procesando")
else:
    print("   ❌ No se encontró proceso")
    sys.exit(1)

# 2. Verificar conexiones de red
print("\n2️⃣  CONEXIONES DE RED:")
try:
    connections = ingest_proc.net_connections()
    print(f"   Total de conexiones: {len(connections)}")
    
    openai_conns = []
    supabase_conns = []
    other_conns = []
    
    for conn in connections:
        if conn.status == 'ESTABLISHED':
            addr = str(conn.remote_address)
            # OpenAI usa api.openai.com o IPs específicas
            if 'openai' in addr.lower() or any(ip in addr for ip in ['52.152', '20.14.246']):
                openai_conns.append(conn)
            elif 'supabase' in addr.lower() or 'postgres' in addr.lower():
                supabase_conns.append(conn)
            else:
                other_conns.append(conn)
    
    print(f"   Conexiones a OpenAI: {len(openai_conns)}")
    print(f"   Conexiones a Supabase: {len(supabase_conns)}")
    print(f"   Otras conexiones: {len(other_conns)}")
    
    if openai_conns:
        print(f"   ✅ Hay conexiones activas con OpenAI")
        for conn in openai_conns[:3]:  # Mostrar primeras 3
            print(f"      {conn.remote_address} - {conn.status}")
    else:
        print(f"   ⚠️  NO hay conexiones activas con OpenAI")
        print(f"      Esto puede indicar que está esperando o bloqueado")
    
    if supabase_conns:
        print(f"   ✅ Hay conexiones activas con Supabase")
    else:
        print(f"   ⚠️  NO hay conexiones activas con Supabase")

except Exception as e:
    print(f"   ⚠️  Error obteniendo conexiones: {e}")

# 3. Verificar threads
print("\n3️⃣  THREADS DEL PROCESO:")
try:
    threads = ingest_proc.threads()
    print(f"   Total de threads: {len(threads)}")
    
    if len(threads) > 20:
        print(f"   ✅ Múltiples threads - Está trabajando en paralelo")
    elif len(threads) > 5:
        print(f"   ⚠️  Threads moderados - Puede estar limitado")
    else:
        print(f"   ⚠️  Pocos threads - Puede estar bloqueado")
except Exception as e:
    print(f"   ⚠️  Error obteniendo threads: {e}")

# 4. Verificar archivos abiertos (puede indicar qué está haciendo)
print("\n4️⃣  ARCHIVOS ABIERTOS:")
try:
    open_files = ingest_proc.open_files()
    print(f"   Archivos abiertos: {len(open_files)}")
    
    pdf_files = [f for f in open_files if f.path.lower().endswith('.pdf')]
    if pdf_files:
        print(f"   PDFs abiertos: {len(pdf_files)}")
        print(f"   ✅ Está procesando archivos PDF")
    
    # Verificar si hay archivos de log o temp
    temp_files = [f for f in open_files if 'temp' in f.path.lower() or 'tmp' in f.path.lower()]
    if temp_files:
        print(f"   Archivos temporales: {len(temp_files)}")
except Exception as e:
    print(f"   ⚠️  Error obteniendo archivos: {e}")

# 5. Análisis de lo que puede estar pasando
print("\n" + "=" * 80)
print("🔍 ANÁLISIS")
print("=" * 80)

print("\n💡 POSIBLES ESCENARIOS:")

if cpu < 5 and len(openai_conns) == 0:
    print("\n1️⃣  ESCENARIO: BLOQUEADO O ESPERANDO")
    print("   • CPU muy bajo (0-5%)")
    print("   • No hay conexiones activas con OpenAI")
    print("   • Posibles causas:")
    print("     - Esperando respuesta de una llamada muy lenta")
    print("     - Bloqueado en I/O")
    print("     - Error silencioso")
    print("   💡 ACCIÓN: Revisar logs del proceso o reiniciar")

elif cpu > 50 and len(openai_conns) > 0:
    print("\n2️⃣  ESCENARIO: PROCESANDO ACTIVAMENTE")
    print("   • CPU alto (>50%)")
    print("   • Hay conexiones con OpenAI")
    print("   • Está trabajando, pero puede ser lento por:")
    print("     - Rate limiting de OpenAI")
    print("     - Muchos chunks por batch")
    print("     - Llamadas secuenciales")
    print("   💡 ACCIÓN: Monitorear por más tiempo")

elif cpu > 50 and len(openai_conns) == 0:
    print("\n3️⃣  ESCENARIO: PROCESANDO LOCALMENTE")
    print("   • CPU alto pero sin conexiones a OpenAI")
    print("   • Puede estar:")
    print("     - Cargando/parseando archivos")
    print("     - Procesando texto localmente")
    print("     - Preparando datos para embeddings")
    print("   💡 ACCIÓN: Normal, esperar a que termine esta fase")

else:
    print("\n4️⃣  ESCENARIO: ESTADO INTERMEDIO")
    print("   • CPU moderado")
    print("   • Estado incierto")
    print("   💡 ACCIÓN: Monitorear más tiempo")

# 6. Recomendación basada en el tiempo
print("\n" + "=" * 80)
print("💡 RECOMENDACIÓN")
print("=" * 80)

if uptime > 1200:  # Más de 20 minutos
    print(f"\n⚠️  El proceso lleva {int(uptime//60)} minutos sin completar un batch")
    print(f"   Con batch_size=150, esto es anormal")
    print(f"\n✅ ACCIÓN RECOMENDADA:")
    print(f"   1. Detener el proceso actual")
    print(f"   2. Reducir batch_size a 50-80")
    print(f"   3. Reiniciar el proceso")
    print(f"\n📊 JUSTIFICACIÓN:")
    print(f"   • batch_size=150 genera batches demasiado grandes")
    print(f"   • Miles de chunks = miles de llamadas a OpenAI")
    print(f"   • Esto puede tomar 30+ minutos por batch")
    print(f"   • Con batch_size=50-80, cada batch toma 5-10 minutos")
elif uptime > 600:  # Más de 10 minutos
    print(f"\n⚠️  El proceso lleva {int(uptime//60)} minutos")
    print(f"   Esto puede ser normal con batch_size=150")
    print(f"   Pero es muy lento")
    print(f"\n💡 RECOMENDACIÓN:")
    print(f"   Esperar 10 minutos más")
    print(f"   Si no hay progreso, reducir batch_size")
else:
    print(f"\n✅ El proceso lleva {int(uptime//60)} minutos")
    print(f"   Esto es normal con batch_size=150")
    print(f"   Espera 10-15 minutos más")

print("\n" + "=" * 80)




