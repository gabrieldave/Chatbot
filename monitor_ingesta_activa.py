"""
🔍 MONITOR DE INGESTA ACTIVA
============================

Monitorea el proceso de ingesta actual y notifica cuando termine.
"""

import os
import sys
import time
import psutil
import psycopg2
from psycopg2.extras import RealDictCursor
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
    raise ValueError("Faltan variables de entorno necesarias")

project_ref = SUPABASE_URL.replace("https://", "").replace(".supabase.co", "")
encoded_password = quote_plus(SUPABASE_DB_PASSWORD)
postgres_connection_string = f"postgresql://postgres:{encoded_password}@db.{project_ref}.supabase.co:5432/postgres"

try:
    import config
    collection_name = config.VECTOR_COLLECTION_NAME
except ImportError:
    collection_name = "knowledge"

def get_ingest_processes():
    """Obtiene procesos de ingesta activos"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 'cpu_percent', 'memory_info']):
        try:
            if proc.info['name'] and 'python' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                if any(keyword in cmdline.lower() for keyword in ['ingest', 'optimized_rag', 'parallel_tier3']):
                    processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return processes

def get_indexed_count():
    """Obtiene número de archivos indexados"""
    try:
        conn = psycopg2.connect(postgres_connection_string, connect_timeout=10)
        cur = conn.cursor()
        cur.execute("SET statement_timeout = '30s'")
        
        cur.execute(f"""
            SELECT COUNT(DISTINCT metadata->>'file_name') as count
            FROM vecs.{collection_name}
            WHERE metadata->>'file_name' IS NOT NULL
        """)
        
        result = cur.fetchone()
        count = result[0] if result else 0
        
        cur.close()
        conn.close()
        return count
    except Exception as e:
        print(f"⚠️  Error obteniendo conteo: {e}")
        return None

def get_total_chunks():
    """Obtiene número total de chunks"""
    try:
        conn = psycopg2.connect(postgres_connection_string, connect_timeout=10)
        cur = conn.cursor()
        cur.execute("SET statement_timeout = '30s'")
        
        cur.execute(f"""
            SELECT COUNT(*) as count
            FROM vecs.{collection_name}
        """)
        
        result = cur.fetchone()
        count = result[0] if result else 0
        
        cur.close()
        conn.close()
        return count
    except Exception as e:
        print(f"⚠️  Error obteniendo chunks: {e}")
        return None

def get_recent_documents(limit=5):
    """Obtiene documentos recientes indexados"""
    try:
        conn = psycopg2.connect(postgres_connection_string, connect_timeout=10)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SET statement_timeout = '30s'")
        
        cur.execute(f"""
            SELECT DISTINCT 
                metadata->>'file_name' as file_name,
                COUNT(*) as chunks
            FROM vecs.{collection_name}
            WHERE metadata->>'file_name' IS NOT NULL
            GROUP BY metadata->>'file_name'
            ORDER BY MAX(id) DESC
            LIMIT %s
        """, (limit,))
        
        results = cur.fetchall()
        cur.close()
        conn.close()
        return [dict(row) for row in results]
    except Exception as e:
        print(f"⚠️  Error obteniendo documentos recientes: {e}")
        return []

def monitor_ingesta():
    """Monitorea el proceso de ingesta hasta que termine"""
    print("="*80)
    print("🔍 MONITOR DE INGESTA ACTIVA")
    print("="*80)
    print(f"⏰ Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    last_count = None
    last_chunks = None
    last_update_time = time.time()
    check_interval = 30  # Verificar cada 30 segundos
    no_change_threshold = 300  # 5 minutos sin cambios = terminado
    last_change_time = time.time()
    
    print("📊 Monitoreando proceso de ingesta...")
    print("   (Presiona Ctrl+C para detener el monitor)")
    print()
    
    try:
        while True:
            # Verificar procesos
            processes = get_ingest_processes()
            
            # Verificar progreso en BD
            current_count = get_indexed_count()
            current_chunks = get_total_chunks()
            
            now = time.time()
            elapsed = now - last_update_time
            
            # Mostrar estado
            if processes:
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔄 Proceso ACTIVO")
                for proc in processes:
                    try:
                        cpu = proc.cpu_percent(interval=0.1)
                        mem_mb = proc.memory_info().rss / (1024 * 1024)
                        cmdline = ' '.join(proc.cmdline()[:2]) if proc.cmdline() else 'N/A'
                        print(f"   PID {proc.pid} | CPU: {cpu:.1f}% | RAM: {mem_mb:.1f} MB")
                        print(f"   Comando: {cmdline}")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            else:
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ⚠️  No se detectan procesos de ingesta")
            
            # Mostrar progreso
            if current_count is not None:
                if last_count is not None and current_count != last_count:
                    last_change_time = now
                    print(f"   📚 Archivos indexados: {current_count} (+{current_count - last_count})")
                else:
                    print(f"   📚 Archivos indexados: {current_count}")
                last_count = current_count
            
            if current_chunks is not None:
                if last_chunks is not None and current_chunks != last_chunks:
                    last_change_time = now
                    print(f"   📦 Chunks totales: {current_chunks:,} (+{current_chunks - last_chunks:,})")
                else:
                    print(f"   📦 Chunks totales: {current_chunks:,}")
                last_chunks = current_chunks
            
            # Verificar si terminó
            if not processes:
                # No hay procesos, verificar si hubo cambios recientes
                time_since_change = now - last_change_time
                
                if time_since_change > no_change_threshold:
                    print("\n" + "="*80)
                    print("✅ INGESTA TERMINADA")
                    print("="*80)
                    print(f"⏰ Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"📚 Archivos indexados: {current_count or 'N/A'}")
                    print(f"📦 Chunks totales: {current_chunks or 'N/A':,}")
                    
                    # Mostrar documentos recientes
                    recent_docs = get_recent_documents(limit=10)
                    if recent_docs:
                        print("\n📄 Últimos documentos indexados:")
                        for i, doc in enumerate(recent_docs[:10], 1):
                            print(f"   {i}. {doc['file_name']} ({doc['chunks']} chunks)")
                    
                    print("\n✅ El proceso de ingesta ha terminado correctamente.")
                    print("="*80)
                    break
                else:
                    remaining = int(no_change_threshold - time_since_change)
                    print(f"   ⏳ Esperando {remaining}s más para confirmar finalización...")
            
            # Calcular velocidad si hay cambios
            if last_count and current_count and current_count > last_count:
                time_elapsed = elapsed if elapsed > 0 else 1
                speed = (current_count - last_count) / (time_elapsed / 60)  # archivos/min
                print(f"   ⚡ Velocidad: {speed:.2f} archivos/min")
            
            last_update_time = now
            
            # Esperar antes de siguiente verificación
            time.sleep(check_interval)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Monitor detenido por el usuario")
        print(f"📚 Archivos indexados hasta ahora: {current_count or 'N/A'}")
        print(f"📦 Chunks totales: {current_chunks or 'N/A':,}")
    except Exception as e:
        print(f"\n❌ Error en monitor: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    monitor_ingesta()



