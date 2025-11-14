"""
🔴 VERIFICAR LÍMITES DE SUPABASE
=================================

Verifica si se están excediendo los límites de Supabase y maneja la situación.
"""

import os
import sys
import psutil
import psycopg2
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

def verificar_estado_supabase():
    """Verifica el estado actual de Supabase"""
    print("="*80)
    print("🔴 VERIFICACIÓN DE LÍMITES DE SUPABASE")
    print("="*80)
    print()
    
    problemas_detectados = []
    
    # Verificar conexión y estado
    try:
        conn = psycopg2.connect(postgres_connection_string, connect_timeout=10)
        cur = conn.cursor()
        
        # Verificar tamaño de la base de datos
        print("📊 Verificando tamaño de la base de datos...")
        cur.execute("""
            SELECT 
                pg_size_pretty(pg_database_size(current_database())) as db_size,
                pg_database_size(current_database()) as db_size_bytes
        """)
        result = cur.fetchone()
        if result:
            db_size = result[0]
            db_size_bytes = result[1]
            db_size_gb = db_size_bytes / (1024**3)
            print(f"   Tamaño de BD: {db_size} ({db_size_gb:.2f} GB)")
            
            # Límites típicos de Supabase (ajustar según tu plan)
            # Free: 500 MB, Pro: 8 GB, Team: 8 GB, Enterprise: ilimitado
            limite_gb = 8.0  # Ajustar según tu plan
            porcentaje = (db_size_gb / limite_gb) * 100
            
            print(f"   Límite estimado: {limite_gb} GB")
            print(f"   Uso: {porcentaje:.1f}%")
            
            if porcentaje > 90:
                problemas_detectados.append(f"⚠️  CRÍTICO: Base de datos al {porcentaje:.1f}% de capacidad ({db_size_gb:.2f} GB / {limite_gb} GB)")
            elif porcentaje > 75:
                problemas_detectados.append(f"⚠️  ADVERTENCIA: Base de datos al {porcentaje:.1f}% de capacidad ({db_size_gb:.2f} GB / {limite_gb} GB)")
        
        # Verificar tamaño de tablas
        print("\n📋 Verificando tamaño de tablas principales...")
        cur.execute("""
            SELECT 
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
            FROM pg_tables
            WHERE schemaname IN ('vecs', 'public')
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            LIMIT 10
        """)
        
        tables = cur.fetchall()
        if tables:
            print("   Tablas más grandes:")
            for schema, table, size, size_bytes in tables:
                size_gb = size_bytes / (1024**3)
                print(f"   - {schema}.{table}: {size} ({size_gb:.2f} GB)")
        
        # Verificar conexiones activas
        print("\n🔌 Verificando conexiones activas...")
        cur.execute("""
            SELECT 
                COUNT(*) as total_connections,
                COUNT(*) FILTER (WHERE state = 'active') as active,
                COUNT(*) FILTER (WHERE state = 'idle') as idle
            FROM pg_stat_activity
            WHERE datname = current_database()
        """)
        
        result = cur.fetchone()
        if result:
            total, active, idle = result
            print(f"   Conexiones totales: {total}")
            print(f"   Conexiones activas: {active}")
            print(f"   Conexiones idle: {idle}")
            
            # Límite típico: 60-200 conexiones según plan
            limite_conexiones = 100  # Ajustar según tu plan
            if total > limite_conexiones * 0.9:
                problemas_detectados.append(f"⚠️  ADVERTENCIA: Muchas conexiones ({total} / ~{limite_conexiones})")
        
        # Verificar queries lentas
        print("\n⏱️  Verificando queries activas...")
        cur.execute("""
            SELECT 
                pid,
                state,
                query_start,
                NOW() - query_start as duration,
                LEFT(query, 100) as query_preview
            FROM pg_stat_activity
            WHERE datname = current_database()
            AND state != 'idle'
            AND query_start < NOW() - INTERVAL '10 seconds'
            ORDER BY query_start
            LIMIT 5
        """)
        
        slow_queries = cur.fetchall()
        if slow_queries:
            print(f"   Queries lentas detectadas: {len(slow_queries)}")
            for pid, state, start, duration, query in slow_queries:
                print(f"   - PID {pid}: {duration} ({state})")
                print(f"     Query: {query}...")
        
        cur.close()
        conn.close()
        
    except psycopg2.OperationalError as e:
        if "timeout" in str(e).lower() or "connection" in str(e).lower():
            problemas_detectados.append("❌ CRÍTICO: No se puede conectar a Supabase (posible sobrecarga)")
            print("❌ Error de conexión: La base de datos puede estar sobrecargada")
        else:
            print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Resumen
    print("\n" + "="*80)
    print("📊 RESUMEN:")
    print("="*80)
    
    if problemas_detectados:
        print("⚠️  PROBLEMAS DETECTADOS:")
        for problema in problemas_detectados:
            print(f"   {problema}")
        print()
        print("🔴 RECOMENDACIONES:")
        print("   1. Pausar o reducir la velocidad de ingesta")
        print("   2. Reducir número de workers")
        print("   3. Esperar a que se estabilice la base de datos")
        print("   4. Verificar límites de tu plan de Supabase")
        return True  # Hay problemas
    else:
        print("✅ No se detectaron problemas críticos")
        print("   La base de datos parece estar funcionando normalmente")
        return False  # Sin problemas

def detener_ingesta():
    """Detiene los procesos de ingesta"""
    print("\n" + "="*80)
    print("🛑 DETENIENDO PROCESOS DE INGESTA")
    print("="*80)
    print()
    
    procesos_detenidos = 0
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] and 'python' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                if any(keyword in cmdline.lower() for keyword in ['ingest_parallel_tier3', 'ingest_optimized_rag', 'ingest_optimized_tier3']) and 'monitor' not in cmdline.lower():
                    print(f"🛑 Deteniendo PID {proc.pid}...")
                    proc.terminate()
                    procesos_detenidos += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if procesos_detenidos > 0:
        print(f"\n✅ {procesos_detenidos} proceso(s) detenido(s)")
        print("💡 Espera unos segundos para que terminen limpiamente")
    else:
        print("⚠️  No se encontraron procesos de ingesta para detener")

def main():
    hay_problemas = verificar_estado_supabase()
    
    if hay_problemas:
        print("\n" + "="*80)
        respuesta = input("¿Deseas detener los procesos de ingesta? (s/n): ").lower().strip()
        
        if respuesta == 's' or respuesta == 'si' or respuesta == 'y' or respuesta == 'yes':
            detener_ingesta()
        else:
            print("\n💡 Procesos continuarán. Monitorea el estado de Supabase.")
            print("   Si los problemas persisten, considera reducir workers o pausar manualmente.")

if __name__ == "__main__":
    main()



