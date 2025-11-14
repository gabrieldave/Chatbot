"""
🔍 VERIFICACIÓN RÁPIDA DEL ESTADO DE INGESTA
============================================

Verifica el estado actual del proceso de ingesta.
"""

import os
import sys
import psutil
import psycopg2
from datetime import datetime
from urllib.parse import quote_plus
from dotenv import load_dotenv

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
    print("⚠️  Faltan variables de entorno")
    sys.exit(1)

project_ref = SUPABASE_URL.replace("https://", "").replace(".supabase.co", "")
encoded_password = quote_plus(SUPABASE_DB_PASSWORD)
postgres_connection_string = f"postgresql://postgres:{encoded_password}@db.{project_ref}.supabase.co:5432/postgres"

try:
    import config
    collection_name = config.VECTOR_COLLECTION_NAME
except ImportError:
    collection_name = "knowledge"

def check_processes():
    """Verifica procesos de ingesta"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_info', 'create_time']):
        try:
            if proc.info['name'] and 'python' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                if any(keyword in cmdline.lower() for keyword in ['ingest', 'optimized_rag', 'parallel_tier3']):
                    processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return processes

def get_stats():
    """Obtiene estadísticas de la base de datos"""
    try:
        conn = psycopg2.connect(postgres_connection_string, connect_timeout=15)
        cur = conn.cursor()
        cur.execute("SET statement_timeout = '20s'")
        
        # Archivos únicos
        cur.execute(f"""
            SELECT COUNT(DISTINCT metadata->>'file_name') as count
            FROM vecs.{collection_name}
            WHERE metadata->>'file_name' IS NOT NULL
        """)
        files_count = cur.fetchone()[0] if cur.rowcount > 0 else 0
        
        # Chunks totales
        cur.execute(f"""
            SELECT COUNT(*) as count
            FROM vecs.{collection_name}
        """)
        chunks_count = cur.fetchone()[0] if cur.rowcount > 0 else 0
        
        cur.close()
        conn.close()
        return files_count, chunks_count
    except Exception as e:
        return None, None

def main():
    print("="*80)
    print("🔍 VERIFICACIÓN DEL ESTADO DE INGESTA")
    print("="*80)
    print(f"⏰ Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Verificar procesos
    processes = check_processes()
    
    if processes:
        print(f"🔄 PROCESOS ACTIVOS: {len(processes)}")
        print()
        for i, proc in enumerate(processes, 1):
            try:
                cpu = proc.cpu_percent(interval=0.1)
                mem_mb = proc.memory_info().rss / (1024 * 1024)
                cmdline = ' '.join(proc.cmdline()[:2]) if proc.cmdline() else 'N/A'
                uptime = datetime.now().timestamp() - proc.create_time()
                hours = int(uptime // 3600)
                minutes = int((uptime % 3600) // 60)
                
                print(f"   {i}. PID {proc.pid}")
                print(f"      Comando: {cmdline}")
                print(f"      CPU: {cpu:.1f}% | RAM: {mem_mb:.1f} MB")
                print(f"      Tiempo activo: {hours}h {minutes}m")
                print()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    else:
        print("⚠️  NO se detectan procesos de ingesta activos")
        print()
    
    # Verificar progreso
    files_count, chunks_count = get_stats()
    
    if files_count is not None:
        print(f"📚 Archivos indexados: {files_count}")
    else:
        print("⚠️  No se pudo obtener conteo de archivos")
    
    if chunks_count is not None:
        print(f"📦 Chunks totales: {chunks_count:,}")
    else:
        print("⚠️  No se pudo obtener conteo de chunks")
    
    print()
    print("="*80)
    
    if processes:
        print("✅ INGESTA EN PROCESO")
        print()
        print("💡 Para monitorear continuamente, ejecuta:")
        print("   python monitor_ingesta_simple.py")
    else:
        print("✅ NO HAY PROCESOS DE INGESTA ACTIVOS")
        print()
        print("💡 Si esperabas que hubiera un proceso, verifica:")
        print("   1. Si el proceso terminó correctamente")
        print("   2. Si hubo algún error")
        print("   3. Si el proceso se detuvo manualmente")

if __name__ == "__main__":
    main()



