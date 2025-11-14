"""
✅ VERIFICAR SI LA INGESTA TERMINÓ
===================================

Verifica si la ingesta terminó correctamente y si hay procesos duplicados.
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

def get_ingest_processes():
    """Obtiene procesos de ingesta"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_info', 'create_time']):
        try:
            if proc.info['name'] and 'python' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                # Buscar procesos de ingesta (excluir monitores y scripts de verificación)
                keywords = ['ingest_optimized_rag', 'ingest_parallel_tier3', 'ingest_optimized_tier3']
                exclude = ['monitor', 'verificar', 'contar', 'barra']
                if any(k in cmdline.lower() for k in keywords) and not any(e in cmdline.lower() for e in exclude):
                    processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return processes

def get_chunks_count():
    """Obtiene conteo de chunks"""
    try:
        conn = psycopg2.connect(postgres_connection_string, connect_timeout=15)
        cur = conn.cursor()
        cur.execute("SET statement_timeout = '20s'")
        
        cur.execute("""
            SELECT n_live_tup
            FROM pg_stat_user_tables
            WHERE schemaname = 'vecs' AND relname = %s
        """, (collection_name,))
        
        result = cur.fetchone()
        count = result[0] if result and result[0] else 0
        
        cur.close()
        conn.close()
        return count
    except:
        return None

def verificar_cambios():
    """Verifica si hay cambios en los últimos minutos"""
    print("🔄 Verificando cambios en los últimos 2 minutos...")
    
    chunks1 = get_chunks_count()
    if chunks1 is None:
        return None
    
    time.sleep(30)  # Esperar 30 segundos
    
    chunks2 = get_chunks_count()
    if chunks2 is None:
        return None
    
    cambio = chunks2 - chunks1
    return cambio

def main():
    print("="*80)
    print("✅ VERIFICACIÓN: ¿TERMINÓ LA INGESTA?")
    print("="*80)
    print(f"⏰ Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Verificar procesos
    processes = get_ingest_processes()
    
    print(f"🔍 Procesos de ingesta detectados: {len(processes)}")
    print()
    
    if processes:
        print("🔄 PROCESOS ACTIVOS ENCONTRADOS:")
        print()
        for i, proc in enumerate(processes, 1):
            try:
                cpu = proc.cpu_percent(interval=0.2)
                mem_mb = proc.memory_info().rss / (1024 * 1024)
                uptime = datetime.now().timestamp() - proc.create_time()
                hours = int(uptime // 3600)
                minutes = int((uptime % 3600) // 60)
                cmdline = ' '.join(proc.cmdline()[:2]) if proc.cmdline() else 'N/A'
                
                print(f"   {i}. PID {proc.pid}")
                print(f"      Script: {cmdline}")
                print(f"      CPU: {cpu:.1f}%")
                print(f"      RAM: {mem_mb:.0f} MB")
                print(f"      Uptime: {hours}h {minutes}m")
                print()
                
                # Si CPU es muy bajo, puede estar terminando
                if cpu < 1.0:
                    print(f"      ⚠️  CPU muy bajo ({cpu:.1f}%) - puede estar terminando")
                    print()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                print(f"   {i}. PID {proc.pid} - Error obteniendo info")
                print()
        
        print("⚠️  HAY PROCESOS ACTIVOS - La ingesta NO ha terminado")
        print()
        print("💡 Si crees que debería haber terminado:")
        print("   1. Verifica que no estén bloqueados")
        print("   2. Espera unos minutos más")
        print("   3. Si están con CPU 0%, pueden estar terminando")
        
    else:
        print("✅ NO se detectan procesos de ingesta activos")
        print()
        
        # Verificar si hay cambios recientes
        print("🔄 Verificando si hay actividad reciente...")
        cambio = verificar_cambios()
        
        if cambio is not None:
            if cambio > 0:
                print(f"⚠️  Se detectaron {cambio} chunks nuevos en los últimos 30 segundos")
                print("   La ingesta puede estar corriendo en otro proceso o aún hay actividad")
            else:
                print("✅ No hay cambios recientes - La ingesta parece haber terminado")
        else:
            print("⚠️  No se pudo verificar cambios (timeout)")
        
        print()
        print("✅ CONCLUSIÓN: La ingesta parece haber TERMINADO")
        print()
        print("📊 Estadísticas finales:")
        chunks = get_chunks_count()
        if chunks:
            estimated_files = chunks // 100
            print(f"   📦 Chunks totales: {chunks:,}")
            print(f"   📚 Archivos estimados: ~{estimated_files:,}")
    
    print()
    print("="*80)
    print("🔍 VERIFICACIÓN DE DUPLICADOS:")
    print("="*80)
    
    # Verificar si hay múltiples procesos del mismo script
    script_counts = {}
    for proc in processes:
        try:
            cmdline = ' '.join(proc.cmdline()[:2]) if proc.cmdline() else 'unknown'
            script_name = cmdline.split()[-1] if cmdline else 'unknown'
            if script_name in script_counts:
                script_counts[script_name] += 1
            else:
                script_counts[script_name] = 1
        except:
            pass
    
    hay_duplicados = False
    for script, count in script_counts.items():
        if count > 1:
            print(f"⚠️  DUPLICADO: {script} está corriendo {count} veces")
            hay_duplicados = True
    
    if not hay_duplicados and processes:
        print("✅ No se detectaron procesos duplicados")
    elif not processes:
        print("✅ No hay procesos activos (no hay duplicados)")
    
    print()
    print("="*80)

if __name__ == "__main__":
    main()



