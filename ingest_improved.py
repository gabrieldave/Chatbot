import os
import sys
from urllib.parse import quote_plus
from dotenv import load_dotenv
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext, Document
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.supabase import SupabaseVectorStore
import time
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import config

# Configurar encoding para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Función para obtener variables de entorno manejando BOM y comillas
def get_env(key):
    """Obtiene una variable de entorno, manejando BOM y variaciones de nombre"""
    value = os.getenv(key, "")
    if not value:
        # Intentar con posibles variaciones (BOM, espacios, etc.)
        for env_key in os.environ.keys():
            if env_key.strip().lstrip('\ufeff') == key:
                value = os.environ[env_key]
                break
    return value.strip('"').strip("'").strip()

# Obtener las variables de entorno
SUPABASE_URL = get_env("SUPABASE_URL")
SUPABASE_SERVICE_KEY = get_env("SUPABASE_SERVICE_KEY")
OPENAI_API_KEY = get_env("OPENAI_API_KEY")
SUPABASE_DB_PASSWORD = get_env("SUPABASE_DB_PASSWORD")

# Verificar que las variables estén definidas
if not SUPABASE_URL or not SUPABASE_SERVICE_KEY or not OPENAI_API_KEY or not SUPABASE_DB_PASSWORD:
    raise ValueError(
        "Faltan variables de entorno. Asegúrate de tener SUPABASE_URL, "
        "SUPABASE_SERVICE_KEY, OPENAI_API_KEY y SUPABASE_DB_PASSWORD en tu archivo .env"
    )

# Definir el modelo de embedding de OpenAI
embed_model = OpenAIEmbedding(model="text-embedding-3-small")

# Extraer el project_ref de la URL de Supabase
project_ref = SUPABASE_URL.replace("https://", "").replace(".supabase.co", "")

# Construir la cadena de conexión completa
encoded_password = quote_plus(SUPABASE_DB_PASSWORD)
postgres_connection_string = f"postgresql://postgres:{encoded_password}@db.{project_ref}.supabase.co:5432/postgres"

# Definir el almacén de vectores (Vector Store) apuntando a Supabase
vector_store = SupabaseVectorStore(
    postgres_connection_string=postgres_connection_string,
    collection_name=config.VECTOR_COLLECTION_NAME
)

# Crear el contexto de almacenamiento (Storage Context)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

print("=" * 80)
print("INGESTIÓN MEJORADA DE DOCUMENTOS")
print("=" * 80)
print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Paso 1: Cargar el índice existente (si existe)
print("1. Cargando índice existente...")
try:
    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        embed_model=embed_model
    )
    print("   ✓ Índice existente cargado (se agregarán nuevos documentos)")
except Exception as e:
    print(f"   ⚠ No se pudo cargar índice existente (se creará uno nuevo): {e}")
    index = None

# Paso 2: Obtener lista de archivos ya indexados
print("\n2. Verificando archivos ya indexados...")

indexed_files = set()
try:
    conn = psycopg2.connect(postgres_connection_string)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(f"""
        SELECT DISTINCT metadata->>'file_name' as file_name
        FROM vecs.{config.VECTOR_COLLECTION_NAME} 
        WHERE metadata->>'file_name' IS NOT NULL
    """)
    for row in cur.fetchall():
        if row['file_name']:
            indexed_files.add(row['file_name'].lower().strip())
    cur.close()
    conn.close()
    print(f"   ✓ Encontrados {len(indexed_files)} archivos ya indexados")
except Exception as e:
    print(f"   ⚠ No se pudo verificar archivos indexados: {e}")
    print("   Continuando sin filtro (puede procesar archivos duplicados)")

# Paso 3: Obtener lista de archivos en la carpeta configurada y filtrar los ya indexados
print(f"\n3. Escaneando archivos en {config.DATA_DIRECTORY}...")
data_dir = config.DATA_DIRECTORY
supported_extensions = {'.pdf', '.epub', '.txt', '.docx', '.md'}

file_list = []
skipped_count = 0
if os.path.exists(data_dir):
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            file_ext = os.path.splitext(file)[1].lower()
            if file_ext in supported_extensions:
                file_path = os.path.join(root, file)
                file_name = os.path.basename(file_path)
                
                # Verificar si el archivo ya está indexado
                if file_name.lower().strip() in indexed_files:
                    skipped_count += 1
                    continue
                
                file_list.append(file_path)

total_files = len(file_list)
print(f"   ✓ Encontrados {total_files} archivos nuevos para procesar")
if skipped_count > 0:
    print(f"   ⏭️  Omitidos {skipped_count} archivos ya indexados")
print(f"   - PDFs: {len([f for f in file_list if f.lower().endswith('.pdf')])}")
print(f"   - EPUBs: {len([f for f in file_list if f.lower().endswith('.epub')])}")
print(f"   - TXTs: {len([f for f in file_list if f.lower().endswith('.txt')])}")
print(f"   - Otros: {len([f for f in file_list if not any(f.lower().endswith(ext) for ext in ['.pdf', '.epub', '.txt'])])}")

if total_files == 0:
    print("\n✅ Todos los archivos ya están indexados. No hay nada nuevo que procesar.")
    sys.exit(0)

# Paso 4: Procesar archivos en lotes con progreso
print("\n4. Procesando archivos nuevos...")
print("=" * 80)

batch_size = 10  # Procesar en lotes de 10 archivos
processed_count = 0
failed_count = 0
start_time = time.time()

# Procesar archivos en lotes
for i in range(0, total_files, batch_size):
    batch = file_list[i:i + batch_size]
    batch_num = (i // batch_size) + 1
    total_batches = (total_files + batch_size - 1) // batch_size
    
    print(f"\n📦 Lote {batch_num}/{total_batches} ({len(batch)} archivos)")
    
    try:
        # Cargar documentos del lote
        batch_start = time.time()
        reader = SimpleDirectoryReader(input_files=batch)
        documents = reader.load_data()
        
        load_time = time.time() - batch_start
        print(f"   ✓ Cargados {len(documents)} documentos en {load_time:.1f}s")
        
        # Agregar documentos al índice
        if index is None:
            # Crear nuevo índice con el primer lote
            print("   📝 Creando nuevo índice...")
            index = VectorStoreIndex.from_documents(
                documents,
                storage_context=storage_context,
                embed_model=embed_model,
                show_progress=True
            )
            print("   ✓ Índice creado")
        else:
            # Agregar al índice existente
            print("   📝 Agregando documentos al índice existente...")
            try:
                # Intentar usar insert si está disponible
                if hasattr(index, 'insert'):
                    for doc in documents:
                        index.insert(doc)
                    print("   ✓ Documentos agregados usando insert()")
                else:
                    # Usar from_documents que agregará al índice existente automáticamente
                    VectorStoreIndex.from_documents(
                        documents,
                        storage_context=storage_context,
                        embed_model=embed_model
                    )
                    print("   ✓ Documentos agregados usando from_documents()")
            except Exception as e:
                # Fallback: usar from_documents directamente
                print(f"   ⚠ Error con insert, usando alternativa: {e}")
                VectorStoreIndex.from_documents(
                    documents,
                    storage_context=storage_context,
                    embed_model=embed_model
                )
                print("   ✓ Documentos agregados")
        
        processed_count += len(batch)
        elapsed_time = time.time() - start_time
        progress = (processed_count / total_files) * 100
        rate = processed_count / elapsed_time if elapsed_time > 0 else 0
        remaining = total_files - processed_count
        eta_seconds = remaining / rate if rate > 0 else 0
        
        print(f"   📊 Progreso: {processed_count}/{total_files} ({progress:.1f}%)")
        if rate > 0:
            print(f"   ⏱️  Velocidad: {rate:.2f} archivos/seg | ETA: {int(eta_seconds//60)}m {int(eta_seconds%60)}s")
        
    except Exception as e:
        failed_count += len(batch)
        print(f"   ✗ Error procesando lote: {e}")
        import traceback
        traceback.print_exc()
        # Continuar con el siguiente lote
        continue

# Resumen final
print("\n" + "=" * 80)
print("RESUMEN FINAL")
print("=" * 80)
total_time = time.time() - start_time
hours = int(total_time // 3600)
minutes = int((total_time % 3600) // 60)
seconds = int(total_time % 60)

print(f"Archivos procesados exitosamente: {processed_count}/{total_files}")
if failed_count > 0:
    print(f"Archivos con errores: {failed_count}")
print(f"Tiempo total: {hours}h {minutes}m {seconds}s")
print(f"Velocidad promedio: {processed_count/total_time:.2f} archivos/segundo" if total_time > 0 else "N/A")
print(f"\n✅ Proceso completado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

