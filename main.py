import os
import sys
from urllib.parse import quote_plus
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from llama_index.core import VectorStoreIndex
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.supabase import SupabaseVectorStore
from supabase import create_client
import litellm
import uvicorn
from typing import Optional
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
DEEPSEEK_API_KEY = get_env("DEEPSEEK_API_KEY")  # Opcional, LiteLLM puede usar la key directamente
ANTHROPIC_API_KEY = get_env("ANTHROPIC_API_KEY")  # Para Claude
GOOGLE_API_KEY = get_env("GOOGLE_API_KEY")  # Para Gemini
COHERE_API_KEY = get_env("COHERE_API_KEY")  # Para Cohere

# Verificar que las variables estén definidas
if not SUPABASE_URL or not SUPABASE_SERVICE_KEY or not OPENAI_API_KEY or not SUPABASE_DB_PASSWORD:
    raise ValueError(
        "Faltan variables de entorno. Asegúrate de tener SUPABASE_URL, "
        "SUPABASE_SERVICE_KEY, OPENAI_API_KEY y SUPABASE_DB_PASSWORD en tu archivo .env"
    )

# Configurar las API keys en las variables de entorno para LiteLLM
# LiteLLM detecta automáticamente las API keys desde variables de entorno
if OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
if DEEPSEEK_API_KEY:
    os.environ["DEEPSEEK_API_KEY"] = DEEPSEEK_API_KEY
if ANTHROPIC_API_KEY:
    os.environ["ANTHROPIC_API_KEY"] = ANTHROPIC_API_KEY
if GOOGLE_API_KEY:
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
if COHERE_API_KEY:
    os.environ["COHERE_API_KEY"] = COHERE_API_KEY

# Verificar si hay un modelo configurado manualmente (tiene prioridad)
chat_model_env = get_env("CHAT_MODEL")
if chat_model_env:
    # Si el modelo configurado es deepseek pero queremos usar ChatGPT, cambiar
    if "deepseek" in chat_model_env.lower() and OPENAI_API_KEY:
        print(f"⚠ CHAT_MODEL está configurado como {chat_model_env}, pero se usará ChatGPT porque OPENAI_API_KEY está disponible")
        modelo_por_defecto = "gpt-3.5-turbo"
        print(f"✓ Usando OpenAI/ChatGPT: {modelo_por_defecto}")
    else:
        print(f"✓ Modelo configurado manualmente en CHAT_MODEL: {chat_model_env}")
        modelo_por_defecto = chat_model_env
else:
    # Si no hay CHAT_MODEL, priorizar ChatGPT si está disponible
    if OPENAI_API_KEY:
        modelo_por_defecto = "gpt-3.5-turbo"
        print(f"✓ Usando OpenAI/ChatGPT como modelo por defecto: {modelo_por_defecto}")
        print(f"✓ API Key de OpenAI configurada")
    elif DEEPSEEK_API_KEY:
        modelo_por_defecto = "deepseek-chat"
        preview_key = DEEPSEEK_API_KEY[:10] if len(DEEPSEEK_API_KEY) >= 10 else DEEPSEEK_API_KEY[:len(DEEPSEEK_API_KEY)]
        print(f"✓ API Key de Deepseek configurada (primeros caracteres: {preview_key}...)")
        print(f"✓ Modelo por defecto: {modelo_por_defecto}")
    else:
        # Fallback final
        modelo_por_defecto = "gpt-3.5-turbo"
        print(f"⚠ No hay API keys configuradas, usando {modelo_por_defecto} como fallback")

# Imprimir mensaje de inicio
print("=" * 60)
print("Iniciando motor del chat...")
print(f"Modelo de IA configurado: {modelo_por_defecto}")
print("=" * 60)

# Extraer el project_ref de la URL de Supabase
project_ref = SUPABASE_URL.replace("https://", "").replace(".supabase.co", "")

# Definir el modelo de embedding de OpenAI (mismo que en ingest.py)
embed_model = OpenAIEmbedding(model="text-embedding-3-small")

# Construir la cadena de conexión completa (mismo método que en ingest.py)
encoded_password = quote_plus(SUPABASE_DB_PASSWORD)
postgres_connection_string = f"postgresql://postgres:{encoded_password}@db.{project_ref}.supabase.co:5432/postgres"

# Inicializar el vector store apuntando a la colección existente
vector_store = SupabaseVectorStore(
    postgres_connection_string=postgres_connection_string,
    collection_name=config.VECTOR_COLLECTION_NAME
)

# Cargar el índice desde el vector store existente
index = VectorStoreIndex.from_vector_store(
    vector_store=vector_store,
    embed_model=embed_model
)

# Crear el motor de consulta (Query Engine) con retriever para obtener contexto
query_engine = index.as_query_engine(similarity_top_k=config.SIMILARITY_TOP_K)

# Imprimir mensaje de confirmación
print("¡Motor listo para recibir preguntas!")

# Inicializar cliente de Supabase para autenticación
supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Inicializar FastAPI
app = FastAPI(title=config.API_TITLE, description=config.API_DESCRIPTION)

# Configurar CORS para permitir peticiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Frontend de Next.js
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Función helper para obtener y validar el usuario desde el token JWT
async def get_user(authorization: Optional[str] = Header(None)):
    """
    Valida el token JWT de Supabase y devuelve el objeto usuario.
    Lanza HTTPException 401 si el token es inválido o no está presente.
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Token de autorización requerido. Incluye 'Authorization: Bearer <token>' en los headers."
        )
    
    # Extraer el token del header "Bearer <token>"
    try:
        token = authorization.replace("Bearer ", "").strip()
    except:
        raise HTTPException(
            status_code=401,
            detail="Formato de token inválido. Usa 'Bearer <token>'"
        )
    
    # Validar el token con Supabase
    try:
        user_response = supabase_client.auth.get_user(token)
        if not user_response.user:
            raise HTTPException(
                status_code=401,
                detail="Token inválido o expirado"
            )
        return user_response.user
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Error al validar token: {str(e)}"
        )

# Modelo Pydantic para la entrada de consulta
class QueryInput(BaseModel):
    query: str

# Endpoint POST /chat
@app.post("/chat")
async def chat(query_input: QueryInput, user = Depends(get_user)):
    """
    Endpoint para hacer consultas sobre los documentos indexados.
    
    Requiere autenticación mediante token JWT de Supabase.
    Verifica tokens disponibles, ejecuta la consulta con LiteLLM (Deepseek por defecto),
    y descuenta los tokens usados del perfil del usuario.
    """
    try:
        # Obtener el ID del usuario
        user_id = user.id
        
        # Paso A: Verificar tokens disponibles
        profile_response = supabase_client.table("profiles").select("tokens_restantes").eq("id", user_id).execute()
        
        if not profile_response.data:
            raise HTTPException(
                status_code=404,
                detail="Perfil de usuario no encontrado"
            )
        
        tokens_restantes = profile_response.data[0]["tokens_restantes"]
        
        if tokens_restantes <= 0:
            raise HTTPException(
                status_code=402,
                detail="Tokens agotados. Por favor, recarga."
            )
        
        # Obtener contexto del RAG usando el query engine
        # Usamos retrieve para obtener los nodos relevantes sin generar respuesta aún
        retriever = index.as_retriever(similarity_top_k=config.SIMILARITY_TOP_K)
        nodes = retriever.retrieve(query_input.query)
        
        # Construir el contexto a partir de los nodos recuperados
        contexto = "\n\n".join([node.text for node in nodes])
        
        # Crear el prompt con contexto y pregunta
        prompt = f"""Contexto:
{contexto}

Pregunta: {query_input.query}

Respuesta:"""
        
        # Ejecutar la consulta usando LiteLLM con Deepseek
        # Usar el modelo configurado al inicio (ya tiene prioridad: CHAT_MODEL > Deepseek > OpenAI)
        chat_model = modelo_por_defecto
        if not chat_model:
            # Fallback de seguridad (no debería llegar aquí)
            if DEEPSEEK_API_KEY:
                chat_model = "deepseek-chat"
            else:
                chat_model = "gpt-3.5-turbo"
        
        # Preparar parámetros para LiteLLM
        litellm_params = {
            "model": chat_model,
            "messages": [
                {
                    "role": "system",
                    "content": config.ASSISTANT_DESCRIPTION
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": config.MODEL_TEMPERATURE
        }
        
        # Configurar la API key según el modelo ANTES de hacer la llamada
        # Esto asegura que LiteLLM tenga la key correcta
        
        # Configurar la API key según el modelo
        # LiteLLM detecta automáticamente las API keys desde variables de entorno,
        # pero podemos configurarlas explícitamente si es necesario
        if chat_model.startswith("deepseek") or "deepseek" in chat_model.lower():
            if DEEPSEEK_API_KEY:
                litellm_params["api_key"] = DEEPSEEK_API_KEY
                print(f"✓ API Key de Deepseek configurada")
            else:
                raise HTTPException(
                    status_code=500,
                    detail="DEEPSEEK_API_KEY no está configurada pero se intentó usar Deepseek"
                )
        elif chat_model.startswith("claude") or "anthropic" in chat_model.lower():
            if ANTHROPIC_API_KEY:
                litellm_params["api_key"] = ANTHROPIC_API_KEY
                print(f"✓ API Key de Anthropic (Claude) configurada")
            # LiteLLM también puede usar ANTHROPIC_API_KEY desde variables de entorno
        elif chat_model.startswith("gemini") or "google" in chat_model.lower():
            if GOOGLE_API_KEY:
                litellm_params["api_key"] = GOOGLE_API_KEY
                print(f"✓ API Key de Google (Gemini) configurada")
            # LiteLLM también puede usar GOOGLE_API_KEY desde variables de entorno
        elif chat_model.startswith("command") or "cohere" in chat_model.lower():
            if COHERE_API_KEY:
                litellm_params["api_key"] = COHERE_API_KEY
                print(f"✓ API Key de Cohere configurada")
            # LiteLLM también puede usar COHERE_API_KEY desde variables de entorno
        elif chat_model.startswith("gpt") or "openai" in chat_model.lower():
            if not OPENAI_API_KEY:
                raise HTTPException(
                    status_code=500,
                    detail="OPENAI_API_KEY no está configurada pero se intentó usar OpenAI/ChatGPT"
                )
            # Asegurar que la API key esté en las variables de entorno
            os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
            # También pasarla explícitamente en los parámetros
            litellm_params["api_key"] = OPENAI_API_KEY
            print(f"✓ API Key de OpenAI configurada para {chat_model}")
        # Para otros modelos, LiteLLM intentará detectar la API key automáticamente
        
        # Log para debugging (solo mostrar primeros caracteres de la query)
        print(f"📤 Enviando consulta a {chat_model} (query: {query_input.query[:50]}...)")
        
        try:
            response = litellm.completion(**litellm_params)
            print(f"✓ Respuesta recibida de {chat_model}")
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error al generar respuesta con LiteLLM: {str(e)}"
            )
        
        # Obtener la respuesta y los tokens usados
        respuesta_texto = response.choices[0].message.content
        
        # Extraer información detallada de uso de tokens de LiteLLM
        usage = response.usage if hasattr(response, 'usage') else None
        
        # Inicializar variables de tokens
        input_tokens = 0
        output_tokens = 0
        total_tokens_usados = 0
        
        if usage:
            # LiteLLM puede devolver usage como objeto o dict
            if isinstance(usage, dict):
                # Si es un diccionario
                input_tokens = usage.get('prompt_tokens', usage.get('input_tokens', 0))
                output_tokens = usage.get('completion_tokens', usage.get('output_tokens', 0))
                total_tokens_usados = usage.get('total_tokens', 0)
            else:
                # Si es un objeto
                if hasattr(usage, 'prompt_tokens'):
                    input_tokens = usage.prompt_tokens
                elif hasattr(usage, 'input_tokens'):
                    input_tokens = usage.input_tokens
                
                if hasattr(usage, 'completion_tokens'):
                    output_tokens = usage.completion_tokens
                elif hasattr(usage, 'output_tokens'):
                    output_tokens = usage.output_tokens
                
                if hasattr(usage, 'total_tokens'):
                    total_tokens_usados = usage.total_tokens
            
            # Si total_tokens_usados es 0 pero tenemos input y output, calcularlo
            if total_tokens_usados == 0 and (input_tokens > 0 or output_tokens > 0):
                total_tokens_usados = input_tokens + output_tokens
        
        # Si no se pudieron obtener los tokens, usar un estimado basado en la longitud
        if total_tokens_usados == 0:
            # Estimación aproximada: 1 token ≈ 4 caracteres
            input_tokens = len(prompt) // 4
            output_tokens = len(respuesta_texto) // 4
            total_tokens_usados = max(100, input_tokens + output_tokens)
            print(f"⚠ No se pudo obtener usage de LiteLLM, usando estimación")
        
        # Loggear información detallada de tokens y costos
        print("=" * 60)
        print(f"[INFO] Consulta procesada:")
        print(f"  Modelo: {chat_model}")
        print(f"  Input tokens: {input_tokens}")
        print(f"  Output tokens: {output_tokens}")
        print(f"  Total tokens: {total_tokens_usados}")
        print(f"  Tokens restantes antes: {tokens_restantes}")
        print("=" * 60)
        
        # Usar total_tokens_usados para el descuento (mantener compatibilidad)
        tokens_usados = total_tokens_usados
        
        # Paso B: Descontar tokens de la base de datos
        nuevos_tokens = tokens_restantes - tokens_usados
        try:
            supabase_client.table("profiles").update({
                "tokens_restantes": nuevos_tokens
            }).eq("id", user_id).execute()
            print(f"[INFO] Tokens descontados: {tokens_usados} tokens")
            print(f"[INFO] Tokens restantes después: {nuevos_tokens} tokens")
        except Exception as e:
            # Si falla la actualización, aún devolvemos la respuesta pero registramos el error
            print(f"❌ Error al actualizar tokens: {str(e)}")
        
        # Paso C: Guardar historial de conversación (si la tabla existe)
        try:
            # Guardar mensaje del usuario
            supabase_client.table("conversations").insert({
                "user_id": user_id,
                "message_role": "user",
                "message_content": query_input.query,
                "tokens_used": 0
            }).execute()
            
            # Guardar respuesta del asistente
            supabase_client.table("conversations").insert({
                "user_id": user_id,
                "message_role": "assistant",
                "message_content": respuesta_texto,
                "tokens_used": tokens_usados
            }).execute()
        except Exception as e:
            # Si la tabla no existe o hay error, continuar sin guardar historial
            print(f"Nota: No se pudo guardar historial (puede que la tabla no exista aún): {str(e)}")
        
        # Devolver la respuesta con información de tokens
        return {
            "response": respuesta_texto,
            "tokens_usados": tokens_usados,
            "tokens_restantes": nuevos_tokens
        }
        
    except HTTPException:
        # Re-lanzar excepciones HTTP (como tokens agotados)
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar la consulta: {str(e)}"
        )

# Endpoint raíz para verificar que el servidor está funcionando
@app.get("/")
async def root():
    return {
        "message": "Chat Bot API está funcionando",
        "status": "ready",
        "modelo_ia": modelo_por_defecto or "No configurado",
        "endpoints": {
            "chat": "/chat (POST) - Requiere autenticación",
            "tokens": "/tokens (GET) - Requiere autenticación",
            "tokens_reload": "/tokens/reload (POST) - Requiere autenticación",
            "tokens_reset": "/tokens/reset (POST) - Requiere autenticación",
            "conversations": "/conversations (GET) - Requiere autenticación",
            "health": "/health (GET)",
            "docs": "/docs"
        }
    }

# Endpoint de salud
@app.get("/health")
async def health():
    return {"status": "healthy", "message": "El motor de chat está listo"}

# Endpoint para consultar tokens restantes del usuario
@app.get("/tokens")
async def get_tokens(user = Depends(get_user)):
    """
    Endpoint para consultar los tokens restantes del usuario autenticado.
    """
    try:
        user_id = user.id
        profile_response = supabase_client.table("profiles").select("tokens_restantes, email").eq("id", user_id).execute()
        
        if not profile_response.data:
            raise HTTPException(
                status_code=404,
                detail="Perfil de usuario no encontrado"
            )
        
        tokens_restantes = profile_response.data[0]["tokens_restantes"]
        return {
            "tokens_restantes": tokens_restantes,
            "email": profile_response.data[0]["email"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener tokens: {str(e)}"
        )

# Modelo para recargar tokens
class TokenReloadInput(BaseModel):
    cantidad: int

# Endpoint para recargar tokens
@app.post("/tokens/reload")
async def reload_tokens(token_input: TokenReloadInput, user = Depends(get_user)):
    """
    Endpoint para recargar tokens al perfil del usuario.
    Permite recargar incluso si los tokens están en negativo.
    """
    try:
        user_id = user.id
        
        if token_input.cantidad <= 0:
            raise HTTPException(
                status_code=400,
                detail="La cantidad debe ser mayor a 0"
            )
        
        # Obtener tokens actuales (pueden ser negativos)
        profile_response = supabase_client.table("profiles").select("tokens_restantes").eq("id", user_id).execute()
        
        if not profile_response.data:
            raise HTTPException(
                status_code=404,
                detail="Perfil de usuario no encontrado"
            )
        
        tokens_actuales = profile_response.data[0]["tokens_restantes"]
        # Permitir recarga incluso con tokens negativos
        nuevos_tokens = tokens_actuales + token_input.cantidad
        
        # Si los tokens quedan negativos después de la recarga, establecer mínimo en 0
        # (opcional, puedes comentar esta línea si quieres permitir negativos)
        # nuevos_tokens = max(0, nuevos_tokens)
        
        # Actualizar tokens
        update_response = supabase_client.table("profiles").update({
            "tokens_restantes": nuevos_tokens
        }).eq("id", user_id).execute()
        
        return {
            "mensaje": f"Tokens recargados exitosamente",
            "tokens_anteriores": tokens_actuales,
            "tokens_recargados": token_input.cantidad,
            "tokens_totales": nuevos_tokens
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al recargar tokens: {str(e)}"
        )

# Endpoint de emergencia para resetear tokens (útil para desarrollo)
@app.post("/tokens/reset")
async def reset_tokens(
    user = Depends(get_user), 
    cantidad: int = Query(20000, description="Cantidad de tokens a establecer")
):
    """
    Endpoint de emergencia para resetear tokens a un valor específico.
    Útil cuando los tokens están en negativo y necesitas resetearlos.
    """
    try:
        user_id = user.id
        
        if cantidad < 0:
            raise HTTPException(
                status_code=400,
                detail="La cantidad debe ser mayor o igual a 0"
            )
        
        # Obtener perfil para verificar que existe
        profile_response = supabase_client.table("profiles").select("tokens_restantes").eq("id", user_id).execute()
        
        if not profile_response.data:
            raise HTTPException(
                status_code=404,
                detail="Perfil de usuario no encontrado"
            )
        
        tokens_anteriores = profile_response.data[0]["tokens_restantes"]
        
        # Actualizar tokens directamente
        update_response = supabase_client.table("profiles").update({
            "tokens_restantes": cantidad
        }).eq("id", user_id).execute()
        
        return {
            "mensaje": f"Tokens reseteados exitosamente",
            "tokens_anteriores": tokens_anteriores,
            "tokens_totales": cantidad
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al resetear tokens: {str(e)}"
        )

# Endpoint para obtener historial de conversaciones
@app.get("/conversations")
async def get_conversations(user = Depends(get_user), limit: int = 100):
    """
    Endpoint para obtener el historial de conversaciones del usuario autenticado.
    """
    try:
        user_id = user.id
        
        # Obtener conversaciones ordenadas por fecha de creación (más recientes primero)
        conversations_response = supabase_client.table("conversations").select(
            "id, message_role, message_content, tokens_used, created_at"
        ).eq("user_id", user_id).order("created_at", desc=False).limit(limit).execute()
        
        if not conversations_response.data:
            return {
                "conversations": [],
                "total": 0
            }
        
        return {
            "conversations": conversations_response.data,
            "total": len(conversations_response.data)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener historial: {str(e)}"
        )

# Ejecutar el servidor
if __name__ == "__main__":
    import socket
    
    # Función para encontrar un puerto disponible
    def find_free_port(start_port=8000):
        port = start_port
        while True:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('0.0.0.0', port))
                    return port
            except OSError:
                port += 1
                if port > start_port + 10:  # Limitar búsqueda a 10 puertos
                    raise Exception(f"No se pudo encontrar un puerto disponible entre {start_port} y {start_port + 10}")
    
    # Intentar usar el puerto 8000, si está ocupado buscar uno disponible
    try:
        port = 8000
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('0.0.0.0', port))
        print(f"✓ Puerto {port} disponible")
    except OSError:
        print(f"⚠ Puerto 8000 está ocupado, buscando puerto alternativo...")
        port = find_free_port(8000)
        print(f"✓ Usando puerto alternativo: {port}")
    
    uvicorn.run(app, host="0.0.0.0", port=port)

