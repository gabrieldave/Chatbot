import os
import sys
import time
import subprocess
from urllib.parse import quote_plus
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

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
    print("Error: Faltan variables de entorno")
    sys.exit(1)

# Construir conexión
project_ref = SUPABASE_URL.replace("https://", "").replace(".supabase.co", "")
encoded_password = quote_plus(SUPABASE_DB_PASSWORD)
postgres_connection_string = f"postgresql://postgres:{encoded_password}@db.{project_ref}.supabase.co:5432/postgres"

# Contar archivos en data
def count_files_in_data():
    data_dir = "./data"
    if not os.path.exists(data_dir):
        return 0
    
    supported_extensions = {'.pdf', '.epub', '.txt', '.docx', '.md'}
    count = 0
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            file_ext = os.path.splitext(file)[1].lower()
            if file_ext in supported_extensions:
                count += 1
    return count

# Contar archivos indexados
def count_indexed_files():
    try:
        conn = psycopg2.connect(postgres_connection_string)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT COUNT(DISTINCT metadata->>'file_name') as count
            FROM vecs.knowledge 
            WHERE metadata->>'file_name' IS NOT NULL
        """)
        
        result = cur.fetchone()
        count = result['count'] if result else 0
        
        cur.close()
        conn.close()
        return count
    except Exception as e:
        print(f"Error al contar archivos indexados: {e}")
        return 0

# Verificar si el proceso de ingest.py está corriendo
def is_ingest_running():
    try:
        # En Windows, buscar procesos de Python que ejecuten ingest.py
        result = subprocess.run(
            ['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FO', 'CSV'],
            capture_output=True,
            text=True
        )
        # Verificar si ingest.py está en algún proceso (simplificado)
        # En Windows es más complicado, así que verificaremos por el progreso
        return True  # Asumimos que está corriendo si hay progreso
    except:
        return False

print("=" * 80)
print("MONITOR DE INGESTIÓN")
print("=" * 80)
print("\nMonitoreando el progreso de la ingestión...")
print("Presiona Ctrl+C para detener el monitoreo\n")

total_files = count_files_in_data()
print(f"Total de archivos a procesar: {total_files}")

last_count = 0
start_time = time.time()
check_interval = 30  # Verificar cada 30 segundos

try:
    while True:
        indexed_count = count_indexed_files()
        elapsed_time = time.time() - start_time
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)
        
        if indexed_count > last_count:
            progress = (indexed_count / total_files * 100) if total_files > 0 else 0
            rate = indexed_count / elapsed_time if elapsed_time > 0 else 0
            remaining = (total_files - indexed_count) / rate if rate > 0 else 0
            
            print(f"[{minutes:02d}:{seconds:02d}] Archivos indexados: {indexed_count}/{total_files} ({progress:.1f}%)")
            if rate > 0:
                print(f"         Velocidad: {rate:.2f} archivos/seg | Tiempo estimado restante: {int(remaining//60)} min {int(remaining%60)} seg")
            
            last_count = indexed_count
            
            # Si todos los archivos están indexados, terminar
            if indexed_count >= total_files:
                print("\n" + "=" * 80)
                print("✅ ¡PROCESO COMPLETADO!")
                print("=" * 80)
                print(f"Total de archivos indexados: {indexed_count}")
                print(f"Tiempo total: {int(elapsed_time//60)} minutos {int(elapsed_time%60)} segundos")
                break
        else:
            # Si no hay progreso, mostrar estado
            if elapsed_time > 60:  # Después de 1 minuto sin progreso
                print(f"[{minutes:02d}:{seconds:02d}] Esperando... ({indexed_count} archivos indexados)")
        
        time.sleep(check_interval)
        
except KeyboardInterrupt:
    print("\n\nMonitoreo detenido por el usuario")
    indexed_count = count_indexed_files()
    print(f"\nEstado final: {indexed_count}/{total_files} archivos indexados")

except Exception as e:
    print(f"\nError en el monitoreo: {e}")
    import traceback
    traceback.print_exc()

