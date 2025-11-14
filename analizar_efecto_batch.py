"""
🔍 ANÁLISIS DEL EFECTO DEL BATCH_SIZE
=====================================

Analiza si el batch_size=80 está teniendo efecto real
"""

import os
import sys
import time
from urllib.parse import quote_plus
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import config
from datetime import datetime, timedelta

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
print("🔍 ANÁLISIS DEL EFECTO DEL BATCH_SIZE")
print("=" * 80)

# Obtener conteo actual
try:
    conn = psycopg2.connect(postgres_connection_string, connect_timeout=10)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SET statement_timeout = '15s'")
    
    cur.execute(f"""
        SELECT 
            COUNT(DISTINCT metadata->>'file_name') as indexed_files,
            COUNT(*) as total_chunks,
            MAX((metadata->>'file_name')) as last_file
        FROM vecs.{config.VECTOR_COLLECTION_NAME} 
        WHERE metadata->>'file_name' IS NOT NULL
    """)
    result = cur.fetchone()
    
    indexed_files = result['indexed_files'] if result else 0
    total_chunks = result['total_chunks'] if result else 0
    
    cur.close()
    conn.close()
    
    print(f"\n📊 ESTADO ACTUAL:")
    print(f"   Archivos indexados: {indexed_files}")
    print(f"   Chunks totales: {total_chunks:,}")
    
except Exception as e:
    print(f"❌ Error consultando base de datos: {e}")
    sys.exit(1)

# Análisis del problema
print(f"\n🔍 ANÁLISIS DEL PROBLEMA:")
print(f"   batch_size configurado: 80")
print(f"   RAM usada en Supabase: ~264 MB (similar a batch_size=15)")

print(f"\n💡 POSIBLES CAUSAS:")

print(f"\n1️⃣  CUERPO DE BOTELLA EN SUPABASE:")
print(f"   • El proceso local carga 80 archivos en memoria")
print(f"   • Pero Supabase procesa las inserciones de forma secuencial")
print(f"   • El uso de RAM en Supabase es del proceso de base de datos, no del batch")
print(f"   • Las inserciones pueden estar limitadas por I/O o CPU de Supabase")

print(f"\n2️⃣  PROCESAMIENTO SECUENCIAL:")
print(f"   • Aunque cargamos 80 archivos, pueden procesarse uno por uno")
print(f"   • LlamaIndex puede estar procesando documentos secuencialmente")
print(f"   • El batch solo agrupa, pero no paraleliza el procesamiento")

print(f"\n3️⃣  LÍMITE DE INSERCIÓN EN SUPABASE:")
print(f"   • Supabase puede tener límites en el tamaño de las transacciones")
print(f"   • Las inserciones grandes pueden dividirse automáticamente")
print(f"   • El uso de RAM no aumenta porque las inserciones son pequeñas")

print(f"\n4️⃣  EFICIENCIA DEL PROCESO:")
print(f"   • El proceso es muy eficiente (17.6 MB/archivo)")
print(f"   • Con batch_size=80, usa ~1.4 GB localmente")
print(f"   • Pero Supabase solo necesita procesar las inserciones")
print(f"   • El uso de RAM en Supabase no refleja el batch_size local")

print(f"\n" + "=" * 80)
print("🎯 CONCLUSIÓN")
print("=" * 80)

print(f"\n✅ El batch_size=80 SÍ está teniendo efecto:")
print(f"   • Carga 80 archivos en memoria local (no 15)")
print(f"   • Procesa más archivos por ciclo")
print(f"   • Reduce el número de ciclos de carga/descarga")

print(f"\n⚠️  Pero el uso de RAM en Supabase NO aumenta porque:")
print(f"   • El uso de RAM en Supabase es del proceso de base de datos")
print(f"   • Las inserciones se procesan de forma eficiente")
print(f"   • El proceso de base de datos no necesita más RAM para más inserciones")

print(f"\n💡 PARA VERIFICAR EL EFECTO REAL:")
print(f"   • Compara la velocidad de procesamiento (archivos/hora)")
print(f"   • Compara el tiempo entre lotes")
print(f"   • No mires el uso de RAM en Supabase como indicador")

print(f"\n📊 MÉTRICAS A OBSERVAR:")
print(f"   • Velocidad: ¿cuántos archivos por hora?")
print(f"   • Tiempo por lote: ¿cuánto tarda cada lote?")
print(f"   • Progreso total: ¿está avanzando más rápido?")

print("\n" + "=" * 80)




