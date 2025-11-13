import os
import sys
import time
import subprocess
from urllib.parse import quote_plus
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
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

# Obtener directorio de datos desde config
DATA_DIRECTORY = config.DATA_DIRECTORY if hasattr(config, 'DATA_DIRECTORY') else "./data"
COLLECTION_NAME = config.VECTOR_COLLECTION_NAME if hasattr(config, 'VECTOR_COLLECTION_NAME') else "knowledge"

# Contar archivos en data con información detallada
def get_files_info():
    """Obtiene información detallada de los archivos a procesar"""
    if not os.path.exists(DATA_DIRECTORY):
        return [], {}
    
    supported_extensions = {'.pdf', '.epub', '.txt', '.docx', '.md', '.doc'}
    files_info = []
    files_dict = {}
    
    for root, dirs, files in os.walk(DATA_DIRECTORY):
        for file in files:
            file_ext = os.path.splitext(file)[1].lower()
            if file_ext in supported_extensions:
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path)
                files_info.append({
                    'name': file,
                    'path': file_path,
                    'size': file_size,
                    'extension': file_ext
                })
                files_dict[file] = file_size
    
    return files_info, files_dict

# Contar archivos indexados con detalles
def get_indexed_files_info():
    """Obtiene información detallada de los archivos ya indexados"""
    try:
        conn = psycopg2.connect(postgres_connection_string)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Contar archivos únicos
        cur.execute(f"""
            SELECT 
                COUNT(DISTINCT metadata->>'file_name') as count,
                COUNT(*) as total_chunks
            FROM vecs.{COLLECTION_NAME} 
            WHERE metadata->>'file_name' IS NOT NULL
        """)
        
        result = cur.fetchone()
        count = result['count'] if result else 0
        total_chunks = result['total_chunks'] if result else 0
        
        # Obtener lista de archivos indexados
        cur.execute(f"""
            SELECT DISTINCT metadata->>'file_name' as file_name
            FROM vecs.{COLLECTION_NAME}
            WHERE metadata->>'file_name' IS NOT NULL
            ORDER BY file_name
        """)
        
        indexed_files = [row['file_name'] for row in cur.fetchall()]
        
        cur.close()
        conn.close()
        return count, total_chunks, indexed_files
    except Exception as e:
        print(f"⚠ Error al obtener información de archivos indexados: {e}")
        return 0, 0, []

def count_files_in_data():
    """Cuenta el total de archivos a procesar"""
    files_info, _ = get_files_info()
    return len(files_info)

def count_indexed_files():
    """Cuenta los archivos ya indexados"""
    count, _, _ = get_indexed_files_info()
    return count

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

def format_size(size_bytes):
    """Formatea el tamaño en bytes a formato legible"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def print_progress_bar(current, total, bar_length=50):
    """Imprime una barra de progreso visual"""
    if total == 0:
        return
    percent = current / total
    filled = int(bar_length * percent)
    bar = '█' * filled + '░' * (bar_length - filled)
    return f"[{bar}] {percent*100:.1f}%"

def clear_screen():
    """Limpia la pantalla (compatible con Windows y Unix)"""
    os.system('cls' if os.name == 'nt' else 'clear')

print("=" * 80)
print("📚 MONITOR DE INGESTIÓN DE LIBROS")
print("=" * 80)
print(f"\n📂 Directorio: {DATA_DIRECTORY}")
print(f"🗄️  Colección: {COLLECTION_NAME}")
print(f"🕐 Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("\nMonitoreando el progreso de la ingestión...")
print("Presiona Ctrl+C para detener el monitoreo\n")

# Obtener información inicial
files_info, files_dict = get_files_info()
total_files = len(files_info)
total_size = sum(f['size'] for f in files_info)

print(f"📊 Estadísticas iniciales:")
print(f"   • Total de archivos: {total_files}")
print(f"   • Tamaño total: {format_size(total_size)}")
print(f"   • Tipos de archivo: {', '.join(set(f['extension'] for f in files_info))}")
print("\n" + "=" * 80 + "\n")

last_count = 0
last_chunks = 0
start_time = time.time()
check_interval = 10  # Verificar cada 10 segundos
update_count = 0

try:
    while True:
        indexed_count, total_chunks, indexed_files = get_indexed_files_info()
        elapsed_time = time.time() - start_time
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)
        
        # Limpiar pantalla cada 5 actualizaciones para mejor visualización
        # (solo si no es la primera vez)
        if update_count > 0 and update_count % 5 == 0:
            clear_screen()
            print("=" * 80)
            print("📚 MONITOR DE INGESTIÓN DE LIBROS")
            print("=" * 80)
            print(f"🕐 Tiempo transcurrido: {minutes:02d}:{seconds:02d}")
            print()
        elif update_count == 0:
            # Primera vez: mostrar encabezado sin limpiar
            print("=" * 80)
            print("📚 MONITOR DE INGESTIÓN DE LIBROS")
            print("=" * 80)
            print(f"🕐 Tiempo transcurrido: {minutes:02d}:{seconds:02d}")
            print()
        
        # Calcular progreso
        progress = (indexed_count / total_files * 100) if total_files > 0 else 0
        rate = indexed_count / elapsed_time if elapsed_time > 0 else 0
        remaining = (total_files - indexed_count) / rate if rate > 0 and indexed_count > 0 else 0
        
        # Mostrar barra de progreso
        bar = print_progress_bar(indexed_count, total_files)
        print(f"\n📈 Progreso: {bar}")
        print(f"   Archivos indexados: {indexed_count}/{total_files}")
        print(f"   Chunks totales: {total_chunks:,}")
        
        if rate > 0:
            print(f"   ⚡ Velocidad: {rate:.3f} archivos/seg")
            if remaining > 0:
                rem_min = int(remaining // 60)
                rem_sec = int(remaining % 60)
                print(f"   ⏱️  Tiempo estimado restante: {rem_min} min {rem_sec} seg")
        
        # Mostrar archivos recién indexados
        if indexed_count > last_count:
            new_files = indexed_files[last_count:]
            if new_files:
                print(f"\n✅ Archivos recién indexados ({len(new_files)}):")
                for file in new_files[:5]:  # Mostrar máximo 5
                    file_size = files_dict.get(file, 0)
                    print(f"   • {file} ({format_size(file_size)})")
                if len(new_files) > 5:
                    print(f"   ... y {len(new_files) - 5} más")
        
        # Mostrar archivos pendientes
        if indexed_count < total_files:
            pending_files = [f['name'] for f in files_info if f['name'] not in indexed_files]
            if pending_files:
                print(f"\n⏳ Archivos pendientes ({len(pending_files)}):")
                for file in pending_files[:5]:  # Mostrar máximo 5
                    file_size = files_dict.get(file, 0)
                    print(f"   • {file} ({format_size(file_size)})")
                if len(pending_files) > 5:
                    print(f"   ... y {len(pending_files) - 5} más")
        
        last_count = indexed_count
        last_chunks = total_chunks
        update_count += 1
        
        # Si todos los archivos están indexados, terminar
        if indexed_count >= total_files and total_files > 0:
            clear_screen()
            print("\n" + "=" * 80)
            print("✅ ¡PROCESO COMPLETADO!")
            print("=" * 80)
            print(f"📚 Total de archivos indexados: {indexed_count}")
            print(f"📦 Total de chunks creados: {total_chunks:,}")
            print(f"💾 Tamaño total procesado: {format_size(total_size)}")
            print(f"⏱️  Tiempo total: {int(elapsed_time//60)} minutos {int(elapsed_time%60)} segundos")
            if elapsed_time > 0:
                print(f"⚡ Velocidad promedio: {rate:.3f} archivos/seg")
            print("=" * 80)
            break
        
        time.sleep(check_interval)
        
except KeyboardInterrupt:
    clear_screen()
    print("\n\n⏹️  Monitoreo detenido por el usuario")
    indexed_count, total_chunks, indexed_files = get_indexed_files_info()
    print(f"\n📊 Estado final:")
    print(f"   • Archivos indexados: {indexed_count}/{total_files}")
    print(f"   • Chunks totales: {total_chunks:,}")
    if indexed_files:
        print(f"\n✅ Archivos completados:")
        for file in indexed_files:
            print(f"   • {file}")

except Exception as e:
    print(f"\n❌ Error en el monitoreo: {e}")
    import traceback
    traceback.print_exc()


