"""
🔬 MONITOR DE EXPERIMENTO: Aumento de RAM en Supabase
=====================================================

Este script monitorea el uso de RAM en Supabase antes y después de aumentar a 4 GB
para verificar si el margen de seguridad era real o había más capacidad disponible.
"""

import os
import sys
import time
from urllib.parse import quote_plus
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import psutil
from datetime import datetime
import config

# Configurar encoding para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Cargar variables de entorno
load_dotenv()

def get_env(key):
    """Obtiene una variable de entorno"""
    value = os.getenv(key, "")
    if not value:
        for env_key in os.environ.keys():
            if env_key.strip().lstrip('\ufeff') == key:
                value = os.environ[env_key]
                break
    return value.strip('"').strip("'").strip()

# Obtener variables de entorno
SUPABASE_URL = get_env("SUPABASE_URL")
SUPABASE_DB_PASSWORD = get_env("SUPABASE_DB_PASSWORD")

if not SUPABASE_URL or not SUPABASE_DB_PASSWORD:
    print("❌ Error: Faltan variables de entorno")
    sys.exit(1)

# Construir conexión
project_ref = SUPABASE_URL.replace("https://", "").replace(".supabase.co", "")
encoded_password = quote_plus(SUPABASE_DB_PASSWORD)
postgres_connection_string = f"postgresql://postgres:{encoded_password}@db.{project_ref}.supabase.co:5432/postgres"

# Obtener batch_size actual
def get_current_batch_size():
    try:
        with open('ingest_improved.py', 'r', encoding='utf-8') as f:
            import re
            content = f.read()
            match = re.search(r'batch_size\s*=\s*(\d+)', content)
            if match:
                return int(match.group(1))
    except:
        pass
    return None

print("=" * 80)
print("🔬 MONITOR DE EXPERIMENTO: AUMENTO DE RAM")
print("=" * 80)
print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("\n📋 Objetivo del experimento:")
print("   • Verificar si el margen de seguridad de RAM es real")
print("   • Si al aumentar a 4 GB el uso sube, confirma que había límite")
print("   • Si el uso se mantiene igual, significa que había más capacidad")
print("\n⏱️  Monitoreando cada 30 segundos...")
print("   Presiona Ctrl+C para detener\n")

batch_size = get_current_batch_size()
print(f"📦 batch_size actual: {batch_size}")
print(f"💡 Este valor se mantendrá constante durante el experimento")
print("\n" + "="*80 + "\n")

# Obtener conteo inicial
try:
    conn = psycopg2.connect(postgres_connection_string, connect_timeout=10)
    cur = conn.cursor()
    cur.execute("SET statement_timeout = '15s'")
    
    cur.execute(f"""
        SELECT COUNT(DISTINCT metadata->>'file_name') as count
        FROM vecs.{config.VECTOR_COLLECTION_NAME}
        WHERE metadata->>'file_name' IS NOT NULL
    """)
    initial_count = cur.fetchone()[0]
    cur.close()
    conn.close()
    
    print(f"📚 Archivos indexados al inicio: {initial_count}")
except:
    initial_count = None

check_count = 0
last_count = initial_count

try:
    while True:
        check_count += 1
        current_time = datetime.now()
        
        # Verificar proceso de ingest
        ingest_running = False
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] == 'python.exe' and proc.info['cmdline']:
                    cmdline = ' '.join(proc.info['cmdline'])
                    if 'ingest_improved.py' in cmdline.lower():
                        ingest_running = True
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        print(f"\n[{current_time.strftime('%H:%M:%S')}] Check #{check_count}")
        print(f"   🔄 Proceso de ingest: {'✅ Activo' if ingest_running else '❌ Detenido'}")
        print(f"   📦 batch_size: {batch_size}")
        
        # Obtener conteo actual
        try:
            conn = psycopg2.connect(postgres_connection_string, connect_timeout=10)
            cur = conn.cursor()
            cur.execute("SET statement_timeout = '15s'")
            
            cur.execute(f"""
                SELECT COUNT(DISTINCT metadata->>'file_name') as count
                FROM vecs.{config.VECTOR_COLLECTION_NAME}
                WHERE metadata->>'file_name' IS NOT NULL
            """)
            current_count = cur.fetchone()[0]
            cur.close()
            conn.close()
            
            if last_count is not None:
                progress = current_count - last_count
                if progress > 0:
                    print(f"   ✅ Progreso: {last_count} -> {current_count} (+{progress} archivos)")
                else:
                    print(f"   ⏳ Sin progreso: {current_count} archivos")
            else:
                print(f"   📚 Archivos indexados: {current_count}")
            
            last_count = current_count
            
        except Exception as e:
            print(f"   ⚠️  Error consultando: {e}")
        
        print(f"\n💡 INSTRUCCIONES:")
        print(f"   1. Observa el uso de RAM en el panel de Supabase")
        print(f"   2. Cuando aumentes a 4 GB, verifica si el uso sube")
        print(f"   3. Si sube de ~1.8 GB a ~3.6 GB → Confirma que había límite")
        print(f"   4. Si se mantiene en ~1.8 GB → Había más capacidad disponible")
        
        print(f"\n⏱️  Próxima verificación en 30 segundos...")
        print("="*80)
        
        time.sleep(30)
        
except KeyboardInterrupt:
    print("\n\n" + "="*80)
    print("⏹️  MONITOR DETENIDO")
    print("="*80)
    if last_count is not None and initial_count is not None:
        total_progress = last_count - initial_count
        print(f"\n📊 Resumen del experimento:")
        print(f"   Archivos indexados durante monitoreo: +{total_progress}")
        print(f"   batch_size mantenido: {batch_size}")




