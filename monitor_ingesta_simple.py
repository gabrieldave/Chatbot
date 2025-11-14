"""
🔍 MONITOR SIMPLE DE INGESTA
============================

Versión simplificada que monitorea y notifica cuando termine.
"""

import os
import sys
import time
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
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] and 'python' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                if any(keyword in cmdline.lower() for keyword in ['ingest', 'optimized_rag', 'parallel_tier3']):
                    processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return processes

def get_indexed_stats():
    """Obtiene estadísticas de indexación"""
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
    print("🔍 MONITOR DE INGESTA")
    print("="*80)
    print(f"⏰ Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    last_files = None
    last_chunks = None
    last_change_time = time.time()
    no_change_threshold = 300  # 5 minutos sin cambios = terminado
    check_interval = 30  # Verificar cada 30 segundos
    start_time = time.time()
    
    print("📊 Monitoreando... (Ctrl+C para detener)")
    print()
    
    try:
        iteration = 0
        while True:
            iteration += 1
            now = time.time()
            
            # Verificar procesos
            processes = get_ingest_processes()
            has_process = len(processes) > 0
            
            # Verificar progreso
            files_count, chunks_count = get_indexed_stats()
            
            # Calcular tiempo transcurrido
            elapsed = now - start_time
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            
            # Mostrar estado
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            if has_process:
                status = "🔄 ACTIVO"
                last_change_time = now
            else:
                status = "⏸️  SIN PROCESOS"
            
            print(f"[{timestamp}] {status} | Tiempo: {hours}h {minutes}m {seconds}s")
            
            if files_count is not None:
                if last_files is not None and files_count != last_files:
                    last_change_time = now
                    delta = files_count - last_files
                    print(f"   📚 Archivos: {files_count} (+{delta})")
                else:
                    print(f"   📚 Archivos: {files_count}")
                last_files = files_count
            
            if chunks_count is not None:
                if last_chunks is not None and chunks_count != last_chunks:
                    last_change_time = now
                    delta = chunks_count - last_chunks
                    print(f"   📦 Chunks: {chunks_count:,} (+{delta:,})")
                else:
                    print(f"   📦 Chunks: {chunks_count:,}")
                last_chunks = chunks_count
            
            # Calcular velocidad
            if last_files and files_count and files_count > last_files:
                time_since_last = now - last_change_time if last_change_time else check_interval
                if time_since_last > 0:
                    speed = (files_count - last_files) / (time_since_last / 60)
                    print(f"   ⚡ Velocidad: {speed:.2f} archivos/min")
            
            # Verificar si terminó
            if not has_process:
                time_since_change = now - last_change_time
                if time_since_change > no_change_threshold:
                    print("\n" + "="*80)
                    print("✅ INGESTA TERMINADA")
                    print("="*80)
                    print(f"⏰ Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"⏱️  Tiempo total: {hours}h {minutes}m {seconds}s")
                    print(f"📚 Archivos indexados: {files_count or 'N/A'}")
                    print(f"📦 Chunks totales: {chunks_count or 'N/A':,}")
                    print("\n🎉 ¡El proceso de ingesta ha terminado!")
                    print("="*80)
                    
                    # Sonido de notificación (si está disponible)
                    try:
                        import winsound
                        winsound.Beep(1000, 500)  # Beep de 1000Hz por 500ms
                        winsound.Beep(1500, 500)  # Beep de 1500Hz por 500ms
                    except:
                        pass
                    
                    break
                else:
                    remaining = int(no_change_threshold - time_since_change)
                    print(f"   ⏳ Esperando {remaining}s para confirmar finalización...")
            
            print()  # Línea en blanco
            
            # Esperar antes de siguiente verificación
            time.sleep(check_interval)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Monitor detenido por el usuario")
        if last_files is not None:
            print(f"📚 Archivos indexados: {last_files}")
        if last_chunks is not None:
            print(f"📦 Chunks totales: {last_chunks:,}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()



