"""
👷 VERIFICAR ESTADO DE WORKERS
===============================

Verifica cuántos workers están activos y su estado.
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
    import config_ingesta
    max_workers = config_ingesta.MAX_WORKERS
except ImportError:
    max_workers = 15  # Default

def get_ingest_processes():
    """Obtiene procesos de ingesta activos"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_info', 'create_time', 'num_threads']):
        try:
            if proc.info['name'] and 'python' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                if any(keyword in cmdline.lower() for keyword in ['ingest_parallel_tier3', 'ingest_optimized_rag', 'ingest_optimized_tier3']) and 'monitor' not in cmdline.lower():
                    processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return processes

def get_system_stats():
    """Obtiene estadísticas del sistema"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        return {
            'cpu_total': cpu_percent,
            'memory_total_gb': memory.total / (1024**3),
            'memory_used_gb': memory.used / (1024**3),
            'memory_percent': memory.percent,
            'memory_available_gb': memory.available / (1024**3)
        }
    except:
        return None

def get_chunks_count():
    """Obtiene conteo rápido de chunks"""
    try:
        conn = psycopg2.connect(postgres_connection_string, connect_timeout=15)
        cur = conn.cursor()
        cur.execute("SET statement_timeout = '20s'")
        
        cur.execute("""
            SELECT n_live_tup
            FROM pg_stat_user_tables
            WHERE schemaname = 'vecs' AND relname = 'knowledge'
        """)
        
        result = cur.fetchone()
        count = result[0] if result and result[0] else None
        
        cur.close()
        conn.close()
        return count
    except:
        return None

def format_time(seconds):
    """Formatea tiempo"""
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
    print("👷 ESTADO DE WORKERS DE INGESTA")
    print("="*80)
    print(f"⏰ Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Obtener procesos
    processes = get_ingest_processes()
    
    if not processes:
        print("⚠️  NO se detectan procesos de ingesta activos")
        print()
        print("💡 Los workers pueden estar dentro de un solo proceso Python")
        print("   (ThreadPoolExecutor crea workers como threads, no procesos separados)")
        return
    
    print(f"🔄 PROCESOS DE INGESTA: {len(processes)}")
    print(f"📊 Workers configurados (por proceso): {max_workers}")
    print(f"👷 Total de workers estimados: {len(processes) * max_workers}")
    print()
    
    # Estadísticas del sistema
    system_stats = get_system_stats()
    if system_stats:
        print("💻 RECURSOS DEL SISTEMA:")
        print(f"   CPU Total: {system_stats['cpu_total']:.1f}%")
        print(f"   RAM Total: {system_stats['memory_total_gb']:.1f} GB")
        print(f"   RAM Usada: {system_stats['memory_used_gb']:.1f} GB ({system_stats['memory_percent']:.1f}%)")
        print(f"   RAM Disponible: {system_stats['memory_available_gb']:.1f} GB")
        print()
    
    # Detalles de cada proceso
    total_cpu = 0
    total_ram = 0
    total_threads = 0
    
    print("📋 DETALLES DE PROCESOS:")
    print()
    
    for i, proc in enumerate(processes, 1):
        try:
            cpu = proc.cpu_percent(interval=0.2)
            mem_mb = proc.memory_info().rss / (1024 * 1024)
            mem_gb = mem_mb / 1024
            threads = proc.info.get('num_threads', 'N/A')
            uptime = datetime.now().timestamp() - proc.create_time()
            
            cmdline = ' '.join(proc.cmdline()[:2]) if proc.cmdline() else 'N/A'
            
            print(f"   {i}. PID {proc.pid}")
            print(f"      Script: {cmdline}")
            print(f"      CPU: {cpu:.1f}%")
            print(f"      RAM: {mem_gb:.2f} GB ({mem_mb:.0f} MB)")
            print(f"      Threads: {threads}")
            print(f"      Uptime: {format_time(uptime)}")
            print()
            
            total_cpu += cpu
            total_ram += mem_gb
            if isinstance(threads, int):
                total_threads += threads
            
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            print(f"   {i}. PID {proc.pid} - Error obteniendo info: {e}")
            print()
    
    # Resumen
    print("="*80)
    print("📊 RESUMEN:")
    print(f"   Procesos activos: {len(processes)}")
    print(f"   CPU total (procesos): {total_cpu:.1f}%")
    print(f"   RAM total (procesos): {total_ram:.2f} GB")
    if total_threads > 0:
        print(f"   Threads totales: {total_threads}")
    print()
    
    # Progreso
    chunks_count = get_chunks_count()
    if chunks_count:
        print(f"📦 Chunks indexados: {chunks_count:,}")
        # Estimar archivos
        estimated_files = chunks_count // 100
        print(f"📚 Archivos estimados: ~{estimated_files}")
    else:
        print("📦 Chunks: No disponible (timeout)")
    
    print()
    print("="*80)
    
    # Estado
    if len(processes) > 0:
        print("✅ WORKERS ACTIVOS Y TRABAJANDO")
        print()
        print("💡 Cada proceso puede tener múltiples workers internos (threads)")
        print(f"   Workers por proceso: {max_workers}")
        print(f"   Total estimado de workers: {len(processes) * max_workers}")
    else:
        print("⚠️  NO HAY WORKERS ACTIVOS")

if __name__ == "__main__":
    main()



