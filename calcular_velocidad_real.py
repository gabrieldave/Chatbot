"""
📊 CÁLCULO DE VELOCIDAD REAL CON LÍMITES DE OPENAI
==================================================
"""

import os
import sys
from urllib.parse import quote_plus
from dotenv import load_dotenv
import psycopg2
import config
import re

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

# Leer batch_size real
try:
    with open('ingest_improved.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        batch_size = None
        for line in lines:
            stripped = line.strip()
            if not stripped.startswith('#') and 'batch_size' in stripped:
                match = re.search(r'batch_size\s*=\s*(\d+)', stripped)
                if match:
                    batch_size = int(match.group(1))
                    break
except Exception as e:
    print(f"❌ Error leyendo batch_size: {e}")
    sys.exit(1)

# Contar archivos
data_dir = "./data"
total_files = 0
if os.path.exists(data_dir):
    supported_extensions = {'.pdf', '.epub', '.txt', '.docx', '.md', '.doc'}
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if os.path.splitext(file)[1].lower() in supported_extensions:
                total_files += 1

# Contar indexados
try:
    conn = psycopg2.connect(postgres_connection_string, connect_timeout=10)
    cur = conn.cursor()
    cur.execute("SET statement_timeout = '15s'")
    
    cur.execute(f"""
        SELECT COUNT(DISTINCT metadata->>'file_name') as count
        FROM vecs.{config.VECTOR_COLLECTION_NAME}
        WHERE metadata->>'file_name' IS NOT NULL
    """)
    
    indexed_count = cur.fetchone()[0]
    cur.close()
    conn.close()
    
    remaining = total_files - indexed_count
    progress = (indexed_count / total_files * 100) if total_files > 0 else 0
    
    print("=" * 80)
    print("📊 ESTADO ACTUAL Y PROYECCIÓN")
    print("=" * 80)
    print()
    print(f"📚 PROGRESO:")
    print(f"   • Archivos indexados: {indexed_count}/{total_files} ({progress:.2f}%)")
    print(f"   • Pendientes: {remaining} archivos")
    print()
    print(f"⚙️  CONFIGURACIÓN:")
    print(f"   • batch_size: {batch_size}")
    print(f"   • OpenAI RPM límite: 5,000")
    print(f"   • OpenAI RPM objetivo (80%): 4,000")
    print()
    
    # Cálculo real basado en límites de OpenAI
    # Cada archivo genera ~100-150 requests (promedio ~125)
    # Con batch_size=38: 38 * 125 = 4,750 requests por batch
    # A 4,000 RPM (80% de 5,000): cada batch toma ~1.19 minutos
    
    avg_requests_per_file = 125  # Promedio conservador
    requests_per_batch = batch_size * avg_requests_per_file
    rpm_target = 4000  # 80% de 5,000
    minutes_per_batch = requests_per_batch / rpm_target
    
    batches_remaining = (remaining + batch_size - 1) // batch_size
    total_minutes = batches_remaining * minutes_per_batch
    total_hours = total_minutes / 60
    
    files_per_hour = (batch_size * 60) / minutes_per_batch
    
    print(f"📈 CÁLCULOS:")
    print(f"   • Requests por archivo: ~{avg_requests_per_file}")
    print(f"   • Requests por batch: ~{requests_per_batch:,}")
    print(f"   • Tiempo por batch: ~{minutes_per_batch:.2f} minutos")
    print()
    print(f"⚡ VELOCIDAD:")
    print(f"   • ~{files_per_hour:.1f} archivos/hora")
    print(f"   • ~{files_per_hour/60:.2f} archivos/minuto")
    print()
    print(f"⏱️  ESTIMACIÓN:")
    print(f"   • Lotes restantes: ~{batches_remaining}")
    print(f"   • Tiempo restante: ~{int(total_hours)}h {int(total_minutes % 60)}m")
    print()
    
    if total_hours < 1:
        print(f"✅ ¡Casi terminamos! Menos de 1 hora restante")
    elif total_hours < 3:
        print(f"✅ Buen progreso. Terminaremos en menos de 3 horas")
    else:
        print(f"📊 Proceso en curso. Sigue monitoreando")
    
    print()
    print("=" * 80)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
