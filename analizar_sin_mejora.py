"""
🔍 ANÁLISIS: ¿Por qué no hay mejora en velocidad?
==================================================
"""

import os
import sys
import time
import psutil
from urllib.parse import quote_plus
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import config

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

def get_env(key):
    value = os.getenv(key, "")
    if not value:
        for env_key in os.environ.keys():
            if env_key.strip().lstrip('\ufeff') == key:
                value = os.environ[env_key]
                break
    return value.strip('"').strip("'").strip()

SUPABASE_URL = get_env("SUPABASE_URL")
SUPABASE_DB_PASSWORD = get_env("SUPABASE_DB_PASSWORD")

if not SUPABASE_URL or not SUPABASE_DB_PASSWORD:
    print("❌ Error: Faltan variables de entorno")
    sys.exit(1)

project_ref = SUPABASE_URL.replace("https://", "").replace(".supabase.co", "")
encoded_password = quote_plus(SUPABASE_DB_PASSWORD)
postgres_connection_string = f"postgresql://postgres:{encoded_password}@db.{project_ref}.supabase.co:5432/postgres"

print("=" * 80)
print("🔍 ANÁLISIS: ¿Por qué no hay mejora en velocidad?")
print("=" * 80)

# Obtener datos actuales
try:
    conn = psycopg2.connect(postgres_connection_string, connect_timeout=10)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SET statement_timeout = '15s'")
    
    cur.execute(f"""
        SELECT COUNT(DISTINCT metadata->>'file_name') as count
        FROM vecs.{config.VECTOR_COLLECTION_NAME} 
        WHERE metadata->>'file_name' IS NOT NULL
    """)
    result = cur.fetchone()
    indexed_count = result['count'] if result else 0
    cur.close()
    conn.close()
except Exception as e:
    print(f"❌ Error consultando: {e}")
    sys.exit(1)

# Obtener tiempo de ejecución del proceso
uptime_seconds = 0
for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
    try:
        if proc.info['name'] == 'python.exe' and proc.info['cmdline']:
            cmdline = ' '.join(proc.info['cmdline'])
            if 'ingest_improved.py' in cmdline.lower():
                uptime_seconds = time.time() - proc.info['create_time']
                break
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        continue

print(f"\n📊 DATOS ACTUALES:")
print(f"   Archivos indexados: {indexed_count}")
print(f"   Tiempo de ejecución: {int(uptime_seconds//60)}m {int(uptime_seconds%60)}s")

# Análisis de métricas de Supabase
print(f"\n📊 MÉTRICAS DE SUPABASE (de tu captura):")
print(f"   CPU: 0.94% (¡muy bajo, incluso más que antes!)")
print(f"   IOPS: 0.01 (0.0%)")
print(f"   RAM: 292.68 MB (7.8%)")

print(f"\n" + "=" * 80)
print("🔍 POSIBLES CAUSAS")
print("=" * 80)

print(f"\n1️⃣  PROCESO RECIÉN INICIADO:")
if uptime_seconds < 300:  # Menos de 5 minutos
    print(f"   ⚠️  El proceso solo lleva {int(uptime_seconds//60)} minutos corriendo")
    print(f"   ⚠️  Puede estar en fase inicial (cargando, verificando archivos, etc.)")
    print(f"   💡 Espera 5-10 minutos más para ver la velocidad real")
    print(f"   💡 El CPU bajo puede indicar que está en fase de preparación")

print(f"\n2️⃣  CUERPO DE BOTELLA EN OTRO LUGAR:")
print(f"   ⚠️  El CPU bajó de 6.49% a 0.94% (extraño)")
print(f"   ⚠️  Esto sugiere que el proceso NO está procesando activamente")
print(f"   💡 Posibles causas:")
print(f"      • Esperando I/O de disco local")
print(f"      • Esperando respuesta de API de embeddings")
print(f"      • Procesando archivos muy grandes")
print(f"      • En fase de carga inicial de archivos")

print(f"\n3️⃣  BATCH_SIZE NO ESTÁ SIENDO USADO:")
print(f"   ⚠️  Aunque configuramos batch_size=150, puede que:")
print(f"      • LlamaIndex esté procesando secuencialmente")
print(f"      • Los archivos se carguen pero se procesen uno por uno")
print(f"      • Haya un límite interno en LlamaIndex")

print(f"\n4️⃣  ARCHIVOS PENDIENTES DIFERENTES:")
print(f"   ⚠️  Los archivos restantes pueden ser:")
print(f"      • Más grandes (PDFs complejos)")
print(f"      • Más difíciles de procesar")
print(f"      • Requerir más tiempo por archivo")

print(f"\n" + "=" * 80)
print("💡 RECOMENDACIONES")
print("=" * 80)

if uptime_seconds < 300:
    print(f"\n⏳ ESPERAR MÁS TIEMPO:")
    print(f"   El proceso acaba de iniciar ({int(uptime_seconds//60)} minutos)")
    print(f"   Espera 5-10 minutos más y vuelve a verificar")
    print(f"   Ejecuta: python calcular_velocidad_real.py")
else:
    print(f"\n🔍 VERIFICAR PROCESO:")
    print(f"   1. Verifica que el proceso esté activo y procesando")
    print(f"   2. Revisa los logs del proceso para ver qué está haciendo")
    print(f"   3. Verifica si hay errores o timeouts")
    
    # Calcular velocidad si hay suficiente tiempo
    if uptime_seconds > 60 and indexed_count > 0:
        files_per_hour = (indexed_count / uptime_seconds) * 3600
        print(f"\n📊 VELOCIDAD ACTUAL:")
        print(f"   {files_per_hour:.1f} archivos/hora")
        print(f"   Compara con la velocidad anterior: ~1,384 archivos/hora")

print(f"\n🔧 ACCIONES:")
print(f"   1. Espera 5-10 minutos más")
print(f"   2. Ejecuta: python calcular_velocidad_real.py")
print(f"   3. Verifica el progreso: python check_progress_now.py")
print(f"   4. Si después de 10 minutos no mejora, podemos reducir batch_size")

print("\n" + "=" * 80)




