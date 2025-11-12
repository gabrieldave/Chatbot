import os
import sys
from urllib.parse import quote_plus
from dotenv import load_dotenv
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.supabase import SupabaseVectorStore
import vecs
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

# Verificar que las variables estén definidas
if not SUPABASE_URL or not SUPABASE_SERVICE_KEY or not OPENAI_API_KEY:
    raise ValueError("Faltan variables de entorno. Asegúrate de tener SUPABASE_URL, SUPABASE_SERVICE_KEY y OPENAI_API_KEY en tu archivo .env")

# Definir el modelo de embedding de OpenAI
embed_model = OpenAIEmbedding(model="text-embedding-3-small")

# Extraer el project_ref de la URL de Supabase
# Formato: https://[project_ref].supabase.co
project_ref = SUPABASE_URL.replace("https://", "").replace(".supabase.co", "")

# Para usar SupabaseVectorStore necesitamos la cadena de conexión de PostgreSQL
# La contraseña de la base de datos se encuentra en el panel de Supabase:
# Settings > Database > Connection string > Connection pooling (modo Session)
# Formato: postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres

# Obtener la contraseña de la base de datos
SUPABASE_DB_PASSWORD = get_env("SUPABASE_DB_PASSWORD")

if not SUPABASE_DB_PASSWORD:
    raise ValueError(
        "Falta SUPABASE_DB_PASSWORD en tu archivo .env.\n"
        "Para obtenerla:\n"
        "1. Ve a tu proyecto en Supabase Dashboard\n"
        "2. Settings > Database\n"
        "3. Busca 'Connection string' y selecciona 'Connection pooling' (modo Session)\n"
        "4. Copia la contraseña (la parte después de 'postgres.[PROJECT_REF]:')\n"
        "5. Agrega SUPABASE_DB_PASSWORD='tu_contraseña' a tu archivo .env"
    )

# Construir la cadena de conexión completa
# Codificar la contraseña para manejar caracteres especiales
encoded_password = quote_plus(SUPABASE_DB_PASSWORD)
# Para conexión directa, el usuario es 'postgres', no 'postgres.[PROJECT_REF]'
# Para pooler, el usuario es 'postgres.[PROJECT_REF]'
# Intentar primero con conexión directa
postgres_connection_string = f"postgresql://postgres:{encoded_password}@db.{project_ref}.supabase.co:5432/postgres"

# Definir el almacén de vectores (Vector Store) apuntando a Supabase
vector_store = SupabaseVectorStore(
    postgres_connection_string=postgres_connection_string,
    collection_name=config.VECTOR_COLLECTION_NAME
)

# Crear el contexto de almacenamiento (Storage Context)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

# Imprimir mensaje de carga
print(f"Cargando documentos desde {config.DATA_DIRECTORY}...")

# Cargar todos los documentos de la carpeta configurada
documents = SimpleDirectoryReader(config.DATA_DIRECTORY).load_data()

# Imprimir mensaje de indexación
print("Documentos cargados. Iniciando indexación...")

# Crear el índice, lo cual enviará los datos a Supabase
index = VectorStoreIndex.from_documents(
    documents,
    storage_context=storage_context,
    embed_model=embed_model
)

# Imprimir mensaje final
print("¡Éxito! La ingesta del cerebro está completada.")

