"""
🔍 MONITOR FINAL DE INGESTA
===========================

Monitorea el proceso de ingesta y notifica cuando termine.
Versión mejorada con mejor manejo de timeouts.
"""

import os
import sys
import time
import psutil
import psycopg2
from datetime import datetime, timedelta
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
                # Buscar procesos de ingesta (excluir monitores)
                if any(keyword in cmdline.lower() for keyword in ['ingest_parallel_tier3', 'ingest_optimized_rag', 'ingest_optimized_tier3']) and 'monitor' not in cmdline.lower():
                    processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return processes

def get_indexed_stats():
    """Obtiene estadísticas de indexación con timeout más largo"""
    try:
        conn = psycopg2.connect(postgres_connection_string, connect_timeout=20)
        cur = conn.cursor()
        # Timeout más largo para queries pesadas
        cur.execute("SET statement_timeout = '60s'")
        
        # Intentar obtener archivos únicos
        try:
            cur.execute(f"""
                SELECT COUNT(DISTINCT metadata->>'file_name') as count
                FROM vecs.{collection_name}
                WHERE metadata->>'file_name' IS NOT NULL
            """)
            files_count = cur.fetchone()[0] if cur.rowcount > 0 else 0
        except Exception as e:
            print(f"   ⚠️  Error contando archivos: {e}")
            files_count = None
        
        # Intentar obtener chunks totales (más rápido)
        try:
            cur.execute(f"""
                SELECT COUNT(*) as count
                FROM vecs.{collection_name}
            """)
            chunks_count = cur.fetchone()[0] if cur.rowcount > 0 else 0
        except Exception as e:
            print(f"   ⚠️  Error contando chunks: {e}")
            chunks_count = None
        
        cur.close()
        conn.close()
        return files_count, chunks_count
    except Exception as e:
        print(f"   ⚠️  Error de conexión: {e}")
        return None, None

def format_time(seconds):
    """Formatea tiempo en formato legible"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"

def main():
    print("="*80)
    print("🔍 MONITOR DE INGESTA - NOTIFICARÁ CUANDO TERMINE")
    print("="*80)
    print(f"⏰ Inicio del monitoreo: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("💡 Este monitor verifica cada 30 segundos y te notificará cuando termine.")
    print("   Presiona Ctrl+C para detener el monitor (no detendrá la ingesta).")
    print()
    
    last_files = None
    last_chunks = None
    last_change_time = time.time()
    no_change_threshold = 300  # 5 minutos sin cambios ni procesos = terminado
    check_interval = 30  # Verificar cada 30 segundos
    start_time = time.time()
    last_stats_time = time.time()
    stats_interval = 120  # Obtener stats cada 2 minutos (para no sobrecargar)
    
    iteration = 0
    
    try:
        while True:
            iteration += 1
            now = time.time()
            elapsed = now - start_time
            
            # Verificar procesos
            processes = get_ingest_processes()
            has_process = len(processes) > 0
            
            # Obtener estadísticas solo cada cierto tiempo
            should_get_stats = (now - last_stats_time) >= stats_interval or iteration == 1
            
            if should_get_stats:
                files_count, chunks_count = get_indexed_stats()
                last_stats_time = now
            else:
                files_count, chunks_count = last_files, last_chunks
            
            # Mostrar estado
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            if has_process:
                status = "🔄 PROCESO ACTIVO"
                last_change_time = now
                print(f"[{timestamp}] {status} | Tiempo monitoreando: {format_time(elapsed)}")
                
                # Mostrar info de procesos
                for proc in processes:
                    try:
                        cpu = proc.cpu_percent(interval=0.1)
                        mem_mb = proc.memory_info().rss / (1024 * 1024)
                        proc_uptime = now - proc.create_time()
                        print(f"   PID {proc.pid} | CPU: {cpu:.1f}% | RAM: {mem_mb:.1f} MB | Uptime: {format_time(proc_uptime)}")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            else:
                status = "⏸️  SIN PROCESOS"
                time_since_change = now - last_change_time
                print(f"[{timestamp}] {status} | Sin cambios por: {format_time(time_since_change)}")
            
            # Mostrar estadísticas si están disponibles
            if files_count is not None:
                if last_files is not None and files_count != last_files:
                    last_change_time = now
                    delta = files_count - last_files
                    print(f"   📚 Archivos indexados: {files_count} (+{delta})")
                else:
                    print(f"   📚 Archivos indexados: {files_count}")
                last_files = files_count
            
            if chunks_count is not None:
                if last_chunks is not None and chunks_count != last_chunks:
                    last_change_time = now
                    delta = chunks_count - last_chunks
                    print(f"   📦 Chunks totales: {chunks_count:,} (+{delta:,})")
                else:
                    print(f"   📦 Chunks totales: {chunks_count:,}")
                last_chunks = chunks_count
            
            # Verificar si terminó
            if not has_process:
                time_since_change = now - last_change_time
                if time_since_change > no_change_threshold:
                    print("\n" + "="*80)
                    print("✅ ¡INGESTA TERMINADA!")
                    print("="*80)
                    print(f"⏰ Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"⏱️  Tiempo total de monitoreo: {format_time(elapsed)}")
                    
                    if files_count is not None:
                        print(f"📚 Archivos indexados: {files_count}")
                    if chunks_count is not None:
                        print(f"📦 Chunks totales: {chunks_count:,}")
                    
                    print("\n🎉 ¡El proceso de ingesta ha terminado correctamente!")
                    print("="*80)
                    
                    # Notificación sonora (Windows)
                    try:
                        import winsound
                        for i in range(3):
                            winsound.Beep(1000, 300)
                            time.sleep(0.2)
                    except:
                        pass
                    
                    # Notificación visual
                    print("\n" + "🔔" * 40)
                    print("🔔 NOTIFICACIÓN: INGESTA TERMINADA 🔔")
                    print("🔔" * 40)
                    
                    break
                else:
                    remaining = int(no_change_threshold - time_since_change)
                    print(f"   ⏳ Esperando {remaining}s más para confirmar finalización...")
            
            print()  # Línea en blanco
            
            # Esperar antes de siguiente verificación
            time.sleep(check_interval)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Monitor detenido por el usuario")
        print("💡 La ingesta continúa en segundo plano si hay procesos activos")
        if last_files is not None:
            print(f"📚 Archivos indexados hasta ahora: {last_files}")
        if last_chunks is not None:
            print(f"📦 Chunks totales: {last_chunks:,}")
    except Exception as e:
        print(f"\n❌ Error en monitor: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()



