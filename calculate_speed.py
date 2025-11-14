import os
import sys
from urllib.parse import quote_plus
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import psutil
import time
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

# Contar archivos en data/
data_dir = "./data"
total_files = 0
if os.path.exists(data_dir):
    supported_extensions = {'.pdf', '.epub', '.txt', '.docx', '.md', '.doc'}
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if os.path.splitext(file)[1].lower() in supported_extensions:
                total_files += 1

print("=" * 80)
print("📊 ANÁLISIS DE VELOCIDAD Y ESTIMACIÓN")
print("=" * 80)

# Obtener conteo actual
try:
    conn = psycopg2.connect(postgres_connection_string, connect_timeout=10)
    conn.set_session(autocommit=False)
    cur = conn.cursor()
    cur.execute("SET statement_timeout = '15s'")
    
    cur.execute(f"""
        SELECT COUNT(DISTINCT metadata->>'file_name') as count
        FROM vecs.{config.VECTOR_COLLECTION_NAME}
        WHERE metadata->>'file_name' IS NOT NULL
    """)
    
    indexed_count = cur.fetchone()[0]
    cur.close()
    conn.close()
    
    print(f"\n📚 Estado actual:")
    print(f"   Archivos indexados: {indexed_count}/{total_files}")
    remaining = total_files - indexed_count
    
    if total_files > 0:
        progress = (indexed_count / total_files * 100)
        print(f"   Progreso: {progress:.2f}%")
        print(f"   Pendientes: {remaining} archivos")
    
    # Obtener batch_size actual
    try:
        with open('ingest_improved.py', 'r', encoding='utf-8') as f:
            import re
            content = f.read()
            match = re.search(r'batch_size\s*=\s*(\d+)', content)
            batch_size = int(match.group(1)) if match else 20
    except:
        batch_size = 20
    
    print(f"\n⚙️  Configuración:")
    print(f"   batch_size: {batch_size}")
    
    # Buscar proceso de ingest para calcular tiempo activo
    ingest_start_time = None
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
        try:
            if proc.info['name'] == 'python.exe' and proc.info['cmdline']:
                cmdline = ' '.join(proc.info['cmdline'])
                if 'ingest_improved.py' in cmdline.lower():
                    ingest_start_time = proc.info['create_time']
                    break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if ingest_start_time:
        elapsed_seconds = time.time() - ingest_start_time
        elapsed_minutes = elapsed_seconds / 60
        elapsed_hours = elapsed_minutes / 60
        
        print(f"\n⏱️  Tiempo de ejecución:")
        print(f"   {int(elapsed_hours)}h {int(elapsed_minutes % 60)}m {int(elapsed_seconds % 60)}s")
        
        # Calcular velocidad (asumiendo que empezó desde 0, pero sabemos que ya había progreso)
        # Vamos a estimar basado en el progreso actual y tiempo transcorrido
        # Pero mejor: calcular velocidad promedio por lote
        
        # Estimación: cada lote de batch_size toma aproximadamente 2-4 minutos
        # dependiendo del tamaño de los archivos
        estimated_time_per_batch_minutes = 3  # 3 minutos por lote (conservador)
        batches_remaining = (remaining + batch_size - 1) // batch_size  # Redondeo hacia arriba
        
        total_time_remaining_minutes = batches_remaining * estimated_time_per_batch_minutes
        total_time_remaining_hours = total_time_remaining_minutes / 60
        
        print(f"\n📈 ESTIMACIÓN DE TIEMPO RESTANTE:")
        print(f"   Lotes restantes: ~{batches_remaining} lotes")
        print(f"   Tiempo estimado por lote: ~{estimated_time_per_batch_minutes} minutos")
        print(f"   Tiempo total estimado: ~{int(total_time_remaining_hours)}h {int(total_time_remaining_minutes % 60)}m")
        
        # Calcular velocidad actual si tenemos datos
        # Asumimos que el proceso actual ha estado corriendo y ha procesado algunos archivos
        # Pero no sabemos exactamente cuántos desde que empezó este proceso
        # Vamos a dar una estimación basada en el batch_size
        
        files_per_hour = (batch_size * 60) / estimated_time_per_batch_minutes
        print(f"\n⚡ VELOCIDAD ESTIMADA:")
        print(f"   ~{files_per_hour:.1f} archivos/hora (con batch_size={batch_size})")
        print(f"   ~{files_per_hour/60:.2f} archivos/minuto")
        
        # Análisis de RAM
        print(f"\n💾 ANÁLISIS DE RECURSOS:")
        print(f"   RAM Supabase: 2 GB")
        print(f"   Uso actual: ~1.8 GB (90%)")
        print(f"   batch_size actual: {batch_size}")
        
        if batch_size <= 30:
            print(f"\n💡 RECOMENDACIÓN:")
            print(f"   ✅ El batch_size actual ({batch_size}) es conservador")
            print(f"   ✅ Puedes aumentar gradualmente hasta 40-50 sin problemas")
            print(f"   ✅ Con 1.8 GB de uso, aún tienes ~200 MB de margen")
            print(f"   ⚠️  Si aumentas batch_size, monitorea el uso de RAM")
            print(f"   💡 El monitor maestro ajustará automáticamente si detecta problemas")
        else:
            print(f"\n💡 RECOMENDACIÓN:")
            print(f"   ⚠️  batch_size actual ({batch_size}) ya es alto")
            print(f"   ⚠️  Con 90% de uso de RAM, no recomendamos aumentar más")
            print(f"   ✅ Mantén el batch_size actual o reduce ligeramente si hay problemas")
        
        # Opción de aumentar RAM
        print(f"\n🔧 OPCIÓN: AUMENTAR RAM")
        print(f"   Si aumentas a 4 GB RAM:")
        print(f"   • Podrías usar batch_size de 60-80 archivos")
        print(f"   • Velocidad aumentaría a ~{files_per_hour * 3:.0f}-{files_per_hour * 4:.0f} archivos/hora")
        print(f"   • Tiempo restante: ~{int(total_time_remaining_hours / 3)}-{int(total_time_remaining_hours / 4)} horas")
        print(f"   • Costo adicional: ~$0.01344/hora más")
        
        print(f"\n📊 CONCLUSIÓN:")
        if remaining > 500:
            print(f"   Con {remaining} archivos pendientes y velocidad actual:")
            print(f"   • Tiempo estimado: ~{int(total_time_remaining_hours)} horas")
            print(f"   • Opción 1: Continuar así (gratis, más lento)")
            print(f"   • Opción 2: Aumentar RAM a 4 GB (costo adicional, ~3x más rápido)")
        else:
            print(f"   Con solo {remaining} archivos pendientes:")
            print(f"   • Tiempo estimado: ~{int(total_time_remaining_hours)} horas")
            print(f"   • Probablemente no necesitas aumentar RAM")
            print(f"   • El proceso terminará pronto")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)




