import os
import sys
import re
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Agregar el directorio actual al path de Python para que pueda encontrar módulos locales
# Esto es necesario en Railway donde el path puede ser diferente
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from fastapi import FastAPI, Depends, HTTPException, Header, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from llama_index.core import VectorStoreIndex
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.supabase import SupabaseVectorStore
from supabase import create_client
import litellm
import uvicorn
from typing import Optional, List, Dict
import config

# Configurar encoding para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Configurar logging a archivo
import logging
from datetime import datetime
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backend.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno desde el archivo .env
# IMPORTANTE: Esto debe ejecutarse ANTES de importar módulos que usan variables de entorno
load_dotenv()

# Importar módulo de Stripe (opcional, solo si está configurado)
try:
    # Intentar importar desde lib.stripe
    try:
        from lib.stripe import get_stripe_price_id, is_valid_plan_code, get_plan_code_from_price_id, STRIPE_WEBHOOK_SECRET
    except ImportError as import_err:
        # Si falla, intentar importar directamente desde el archivo
        import importlib.util
        # Intentar múltiples rutas posibles (Railway usa /app, local puede ser diferente)
        possible_paths = [
            os.path.join(current_dir, "lib", "stripe.py"),
            os.path.join("/app", "lib", "stripe.py"),
            "lib/stripe.py",
            "./lib/stripe.py"
        ]
        
        stripe_module = None
        for stripe_path in possible_paths:
            if os.path.exists(stripe_path):
                try:
                    spec = importlib.util.spec_from_file_location("lib.stripe", stripe_path)
                    stripe_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(stripe_module)
                    get_stripe_price_id = stripe_module.get_stripe_price_id
                    is_valid_plan_code = stripe_module.is_valid_plan_code
                    get_plan_code_from_price_id = stripe_module.get_plan_code_from_price_id
                    STRIPE_WEBHOOK_SECRET = stripe_module.STRIPE_WEBHOOK_SECRET
                    logger.info(f"✅ Módulo Stripe cargado desde: {stripe_path}")
                    break
                except Exception as e:
                    logger.debug(f"No se pudo cargar desde {stripe_path}: {e}")
                    continue
        
        if stripe_module is None:
            raise ImportError(f"No se encontró lib/stripe.py. Rutas intentadas: {possible_paths}. Error original: {import_err}")
    
    import stripe
    # Verificar que stripe.api_key esté configurado
    if hasattr(stripe, 'api_key') and stripe.api_key:
        STRIPE_AVAILABLE = True
        logger.info("✅ Stripe configurado correctamente")
    else:
        STRIPE_AVAILABLE = False
        logger.warning("⚠️ Stripe importado pero STRIPE_SECRET_KEY no está configurada")
except (ImportError, ValueError, Exception) as e:
    STRIPE_AVAILABLE = False
    STRIPE_WEBHOOK_SECRET = None
    logger.warning(f"⚠️ Stripe no está disponible: {e}")
    logger.debug(f"Directorio actual: {current_dir}, sys.path: {sys.path}")

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

# Variables de entorno para Stripe (opcionales, solo necesarias si se usa Stripe)
FRONTEND_URL = get_env("FRONTEND_URL") or "http://localhost:3000"

# Verificar que las variables estén definidas
# OPENAI_API_KEY o DEEPSEEK_API_KEY son opcionales (al menos una debe estar)
# SUPABASE_DB_PASSWORD es opcional para el backend (solo se usa en ingesta y RAG)
has_ai_key = bool(OPENAI_API_KEY or DEEPSEEK_API_KEY)
if not SUPABASE_URL or not SUPABASE_SERVICE_KEY or not has_ai_key:
    missing = []
    if not SUPABASE_URL:
        missing.append("SUPABASE_URL")
    if not SUPABASE_SERVICE_KEY:
        missing.append("SUPABASE_SERVICE_KEY")
    if not has_ai_key:
        missing.append("OPENAI_API_KEY o DEEPSEEK_API_KEY (al menos una)")
    raise ValueError(
        f"Faltan variables de entorno obligatorias: {', '.join(missing)}. "
        "Asegúrate de tenerlas configuradas en Railway."
    )

# Verificar si SUPABASE_DB_PASSWORD está configurado para RAG
RAG_AVAILABLE = bool(SUPABASE_DB_PASSWORD)
if not RAG_AVAILABLE:
    logger.warning(
        "SUPABASE_DB_PASSWORD no está configurado. "
        "El sistema RAG (búsqueda en documentos) no estará disponible. "
        "Las funciones de autenticación y otros endpoints seguirán funcionando."
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
    # Para LiteLLM, DeepSeek necesita el formato "deepseek/deepseek-chat"
    # Si el usuario puso solo "deepseek-chat", agregamos el prefijo
    if chat_model_env.lower() == "deepseek-chat" or chat_model_env.lower().startswith("deepseek-chat"):
        chat_model_clean = "deepseek/deepseek-chat"
    elif chat_model_env.lower().startswith("deepseek/"):
        # Ya tiene el formato correcto
        chat_model_clean = chat_model_env.strip()
    else:
        # Otro modelo, usar tal cual
        chat_model_clean = chat_model_env.strip()
    
    # Si CHAT_MODEL está configurado, usarlo SIEMPRE (tiene prioridad absoluta)
    # Respetar la configuración del usuario, NO cambiar a OpenAI aunque esté disponible
    print(f"✓ Modelo configurado manualmente en CHAT_MODEL: {chat_model_clean}")
    modelo_por_defecto = chat_model_clean
else:
    # Si no hay CHAT_MODEL, priorizar DeepSeek si está disponible
    if DEEPSEEK_API_KEY:
        # LiteLLM requiere el formato "deepseek/deepseek-chat"
        modelo_por_defecto = "deepseek/deepseek-chat"
        preview_key = DEEPSEEK_API_KEY[:10] if len(DEEPSEEK_API_KEY) >= 10 else DEEPSEEK_API_KEY[:len(DEEPSEEK_API_KEY)]
        print(f"✓ API Key de Deepseek configurada (primeros caracteres: {preview_key}...)")
        print(f"✓ Modelo por defecto: {modelo_por_defecto}")
    elif OPENAI_API_KEY:
        modelo_por_defecto = "gpt-3.5-turbo"
        print(f"✓ Usando OpenAI/ChatGPT como modelo por defecto: {modelo_por_defecto}")
        print(f"✓ API Key de OpenAI configurada")
    else:
        # Fallback final
        modelo_por_defecto = "gpt-3.5-turbo"
        print(f"⚠ No hay API keys configuradas, usando {modelo_por_defecto} como fallback")

# Imprimir mensaje de inicio
print("=" * 60)
# Inicializar componentes RAG solo si SUPABASE_DB_PASSWORD está configurado
vector_store = None
index = None
query_engine = None
embed_model = None

if RAG_AVAILABLE:
    try:
        logger.info("Iniciando motor del chat...")
        logger.info(f"Modelo de IA configurado: {modelo_por_defecto}")

        # Extraer el project_ref de la URL de Supabase
        project_ref = SUPABASE_URL.replace("https://", "").replace(".supabase.co", "")

        # Definir el modelo de embedding de OpenAI (mismo que en ingest.py)
        embed_model = OpenAIEmbedding(model="text-embedding-3-small")

        # Construir la cadena de conexión completa
        # Railway puede tener problemas con IPv6, intentar múltiples métodos
        encoded_password = quote_plus(SUPABASE_DB_PASSWORD)
        
        # Intentar múltiples métodos de conexión
        # IMPORTANTE: Railway puede usar IPv4, pero Supabase Dedicated Pooler requiere IPv6
        # Por eso intentamos conexión directa PRIMERO (compatible con IPv4)
        connection_strings = [
            # Opción 1: Conexión directa (compatible con IPv4, más confiable)
            f"postgresql://postgres:{encoded_password}@db.{project_ref}.supabase.co:5432/postgres",
            # Opción 2: Connection pooling Shared (si está habilitado, compatible con IPv4)
            # Nota: Dedicated Pooler NO es compatible con IPv4
            f"postgresql://postgres.{project_ref}:{encoded_password}@aws-0-us-west-1.pooler.supabase.com:6543/postgres",
            # Opción 3: Connection pooling región alternativa
            f"postgresql://postgres.{project_ref}:{encoded_password}@aws-0-us-east-1.pooler.supabase.com:6543/postgres",
        ]
        
        vector_store = None
        last_error = None
        
        for i, conn_str in enumerate(connection_strings, 1):
            try:
                host_info = conn_str.split('@')[1].split('/')[0] if '@' in conn_str else 'N/A'
                logger.info(f"Intentando conexión {i}/{len(connection_strings)}: {host_info}")
                
                # Crear vector store con timeout más largo
                vector_store = SupabaseVectorStore(
                    postgres_connection_string=conn_str,
                    collection_name=config.VECTOR_COLLECTION_NAME
                )
                
                # Intentar cargar el índice para verificar la conexión realmente funciona
                # Esto hace una consulta real a la base de datos
                logger.info("Verificando conexión con consulta de prueba...")
                test_index = VectorStoreIndex.from_vector_store(
                    vector_store=vector_store,
                    embed_model=embed_model
                )
                
                logger.info(f"✅ Conexión exitosa con método {i}")
                postgres_connection_string = conn_str
                # Usar el índice de prueba
                index = test_index
                break
            except Exception as e:
                last_error = e
                error_msg = str(e)
                # Log más detallado del error
                if "Network is unreachable" in error_msg:
                    logger.warning(f"⚠️ Método {i} falló: Network unreachable (problema de conectividad de red)")
                elif "password authentication failed" in error_msg.lower():
                    logger.warning(f"⚠️ Método {i} falló: Password incorrecta")
                elif "Tenant or user not found" in error_msg:
                    logger.warning(f"⚠️ Método {i} falló: Connection pooling no configurado o región incorrecta")
                else:
                    logger.warning(f"⚠️ Método {i} falló: {error_msg[:150]}")
                continue
        
        if vector_store is None or index is None:
            error_details = str(last_error) if last_error else "Desconocido"
            raise Exception(
                f"No se pudo conectar a Supabase con ningún método.\n"
                f"Último error: {error_details}\n\n"
                f"SOLUCIÓN:\n"
                f"1. Ve a Supabase Dashboard → Settings → Database\n"
                f"2. Verifica 'Network Restrictions' - debe estar DESHABILITADO\n"
                f"3. Verifica 'Connection pooling' - debe estar HABILITADO\n"
                f"4. Si connection pooling está habilitado, copia la URL completa y verifica la región\n"
                f"5. Reinicia el servicio en Railway después de hacer cambios"
            )

        # Si ya cargamos el índice en el loop anterior, no necesitamos cargarlo de nuevo
        if index is None:
            # Cargar el índice desde el vector store existente
            logger.info("Cargando índice vectorial...")
            index = VectorStoreIndex.from_vector_store(
                vector_store=vector_store,
                embed_model=embed_model
            )

        # Crear el motor de consulta (Query Engine) con retriever para obtener contexto
        query_engine = index.as_query_engine(similarity_top_k=config.SIMILARITY_TOP_K)

        # Imprimir mensaje de confirmación
        logger.info("✅ Sistema RAG inicializado correctamente")
    except Exception as e:
        # Log más detallado del error
        error_msg = str(e)
        logger.error(f"❌ Error al inicializar sistema RAG: {error_msg}")
        
        # Mensaje más específico según el tipo de error
        if "Network is unreachable" in error_msg or "connection" in error_msg.lower():
            logger.warning("⚠️ No se pudo conectar a la base de datos de Supabase. Verifica:")
            logger.warning("   1. Que SUPABASE_DB_PASSWORD esté configurado correctamente en Railway")
            logger.warning("   2. Que el servidor de Supabase esté accesible desde Railway")
            logger.warning("   3. Que no haya restricciones de firewall bloqueando la conexión")
        else:
            logger.warning(f"⚠️ Error desconocido: {error_msg}")
        
        logger.warning("El sistema continuará sin RAG. Las funciones de autenticación y otros endpoints seguirán funcionando.")
        RAG_AVAILABLE = False
        vector_store = None
        index = None
        query_engine = None
        embed_model = None
else:
    logger.info("Sistema RAG deshabilitado (SUPABASE_DB_PASSWORD no configurado)")

# Inicializar cliente de Supabase para autenticación
supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Inicializar FastAPI
app = FastAPI(title=config.API_TITLE, description=config.API_DESCRIPTION)

# Configurar CORS para permitir peticiones desde el frontend
# Obtener FRONTEND_URL de variables de entorno para permitir CORS dinámicamente
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
# Permitir tanto localhost (desarrollo) como el dominio de producción
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "https://codextrader.tech",
    "https://www.codextrader.tech",
]

# Si FRONTEND_URL está configurado y no está en la lista, agregarlo
if frontend_url and frontend_url not in allowed_origins:
    allowed_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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
    conversation_id: Optional[str] = None  # ID de la conversación (opcional, se crea nueva si no se proporciona)
    response_mode: Optional[str] = 'fast'  # 'fast' o 'deep'

# Modelo para crear nueva conversación
class NewConversationInput(BaseModel):
    title: Optional[str] = None  # Título opcional (se genera desde la primera pregunta si no se proporciona)

# Endpoint POST /chat
@app.post("/chat")
async def chat(query_input: QueryInput, user = Depends(get_user)):
    """
    Endpoint para hacer consultas sobre los documentos indexados.
    
    Requiere autenticación mediante token JWT de Supabase.
    Verifica tokens disponibles, ejecuta la consulta con LiteLLM (Deepseek por defecto),
    y descuenta los tokens usados del perfil del usuario.
    """
    
    def is_simple_greeting(message: str) -> bool:
        """
        Detecta si el mensaje es solo un saludo simple sin contenido de trading.
        Retorna True si es solo un saludo, False si contiene contenido de trading.
        """
        # Normalizar el mensaje: minúsculas, sin espacios extra, sin emojis
        normalized = re.sub(r'[^\w\s]', '', message.lower().strip())
        words = normalized.split()
        
        # Si el mensaje es muy largo, probablemente no es solo un saludo
        if len(words) > 5:
            return False
        
        # Lista de saludos simples (español e inglés)
        simple_greetings = [
            'hola', 'hi', 'hello', 'hey',
            'buenas', 'buen', 'día', 'day',
            'qué', 'tal', 'what', 'up',
            'saludos', 'greetings',
            'buenos', 'días', 'mornings', 'afternoon', 'evening',
            'good', 'morning', 'afternoon', 'evening',
            'there', 'hola qué tal', 'hi there', 'hello there', 'hey there'
        ]
        
        # Verificar si todas las palabras son saludos simples
        all_greetings = all(word in simple_greetings for word in words if word)
        
        # Palabras relacionadas con trading que indican que NO es solo un saludo
        trading_keywords = [
            'trading', 'trader', 'mercado', 'market', 'operar', 'trade',
            'estrategia', 'strategy', 'riesgo', 'risk', 'capital', 'money',
            'análisis', 'analysis', 'gráfico', 'chart', 'indicador', 'indicator',
            'soporte', 'support', 'resistencia', 'resistance', 'tendencia', 'trend',
            'compra', 'venta', 'buy', 'sell', 'precio', 'price', 'acción', 'stock',
            'forex', 'crypto', 'bitcoin', 'cripto', 'divisa', 'currency',
            'psicología', 'psychology', 'emociones', 'emotions', 'disciplina', 'discipline',
            'swing', 'scalping', 'intradía', 'intraday', 'day trading', 'daytrading',
            'explicar', 'explain', 'qué es', 'what is', 'cómo', 'how', 'cuál', 'which'
        ]
        
        # Si contiene palabras de trading, NO es solo un saludo
        has_trading_content = any(keyword in normalized for keyword in trading_keywords)
        
        # Es solo un saludo si: todas las palabras son saludos Y no hay contenido de trading
        return all_greetings and not has_trading_content and len(words) > 0
    
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
        
        # Verificar si es solo un saludo simple (evitar búsqueda RAG para acelerar respuesta)
        is_greeting = is_simple_greeting(query_input.query)
        
        if is_greeting:
            # Para saludos simples, saltarse RAG completamente (contexto vacío)
            contexto = ""
        elif not RAG_AVAILABLE or index is None:
            # Si RAG no está disponible, usar contexto vacío
            logger.warning("RAG no disponible, respondiendo sin contexto de documentos")
            contexto = ""
        else:
            # Obtener contexto del RAG usando el query engine
            # Usamos retrieve para obtener los nodos relevantes sin generar respuesta aún
            try:
                retriever = index.as_retriever(similarity_top_k=config.SIMILARITY_TOP_K)
                nodes = retriever.retrieve(query_input.query)
                
                # Construir el contexto a partir de los nodos recuperados
                contexto = "\n\n".join([node.text for node in nodes])
            except Exception as e:
                logger.error(f"Error al recuperar contexto RAG: {e}")
                contexto = ""
        
        # Crear el prompt con contexto y pregunta
        # Si es un saludo, usar un prompt más simple sin contexto RAG
        if is_greeting:
            # Para saludos, el prompt es simplemente el mensaje del usuario
            prompt = query_input.query
        else:
            prompt = f"""Basándote en el siguiente contexto extraído de la biblioteca de trading, proporciona una respuesta COMPLETA y DETALLADA a la pregunta del usuario.

CONTEXTO:
{contexto}

PREGUNTA DEL USUARIO: {query_input.query}

INSTRUCCIONES:
- Proporciona una respuesta COMPLETA, no una respuesta corta
- Explica los conceptos de manera clara y detallada
- Si el contexto menciona estrategias, técnicas o conceptos específicos, explícalos en profundidad
- Incluye ejemplos prácticos cuando sea relevante
- Estructura tu respuesta de manera organizada
- Si hay múltiples aspectos en la pregunta, cubre todos ellos

RESPUESTA DETALLADA:"""
        
        # Ejecutar la consulta usando LiteLLM con Deepseek
        # Usar el modelo configurado al inicio (ya tiene prioridad: CHAT_MODEL > Deepseek > OpenAI)
        chat_model = modelo_por_defecto
        if not chat_model:
            # Fallback de seguridad (no debería llegar aquí)
            if DEEPSEEK_API_KEY:
                chat_model = "deepseek/deepseek-chat"  # Formato correcto para LiteLLM
            else:
                chat_model = "gpt-3.5-turbo"
        
        # REGLA CRÍTICA SOBRE SALUDOS (máxima prioridad, se aplica antes de RAG y modo de respuesta)
        greetings_instruction = """

REGLA CRÍTICA SOBRE SALUDOS (OBEDECE ESTO SIEMPRE):

1. Si el mensaje del usuario es SOLO un saludo o algo social muy corto,

   por ejemplo en español:
   - "hola"
   - "buenas"
   - "buen día"
   - "qué tal"
   - "hey"
   - "saludos"
   - "hola, qué tal"
   - o variaciones similares con o sin emojis,

   o en inglés:
   - "hi"
   - "hello"
   - "hey"
   - "good morning"
   - "good afternoon"
   - "good evening"
   - "what's up"
   - "hi there"
   - "hello there"
   - "hey there"
   - "good day"
   - o variaciones similares con o sin emojis,

   Y NO contiene ninguna palabra relacionada con trading, mercados, dinero, estrategia, gestión de riesgo, análisis, etc.,

   ENTONCES:

   - NO uses el contexto de RAG.
   - NO generes una explicación larga.
   - NO uses encabezados, ni listas, ni markdown complejo.

   En esos casos, responde SOLO con:

   - 1 o 2 frases muy cortas:

     *Primero*, un saludo amable.

     *Segundo*, una frase diciendo en qué puedes ayudar (trading, gestión de riesgo, psicología, estrategias).

     Y termina con una pregunta breve invitando a que el usuario formule su duda.

   Ejemplo de estilo:

     Usuario: "hola"

     Asistente: "¡Hola! Soy Codex Trader, tu asistente de IA especializado en trading. 

     Puedo ayudarte con gestión de riesgo, análisis técnico, psicología del trader y diseño de estrategias. 

     ¿Sobre qué tema de trading te gustaría que empecemos?"

2. Si el mensaje del usuario incluye ya alguna pregunta o tema de trading

   (por ejemplo: "hola, explícame gestión de riesgo" o "hola, qué es el day trading"),

   ENTONCES:

   - Trátalo como una pregunta normal de trading.

   - Aplica el modo de respuesta (Rápida o Estudio profundo) según corresponda.
"""
        
        # Construir instrucción de modo de respuesta según el modo seleccionado
        response_mode = query_input.response_mode or 'fast'
        if response_mode == 'fast':
            mode_instruction = """

═══════════════════════════════════════════════════════════════
MODO: RESPUESTA RÁPIDA (OBLIGATORIO - RESPETA ESTO ESTRICTAMENTE)
═══════════════════════════════════════════════════════════════

RESPUESTA MÁXIMA: 1-2 PÁRRAFOS CORTOS. NADA MÁS.

REGLAS ESTRICTAS:
- Máximo 1-2 párrafos cortos (3-5 oraciones cada uno)
- Ve directo al punto, sin introducciones largas
- NO uses encabezados (##, ###)
- NO uses listas de viñetas extensas
- NO des ejemplos detallados
- NO expliques conceptos secundarios
- Si la pregunta es amplia, menciona solo las ideas principales
- Al final, puedes mencionar brevemente que el usuario puede pedir más detalles si lo desea

EJEMPLO DE LONGITUD CORRECTA:
"La gestión de riesgo es fundamental en trading. Consiste en limitar las pérdidas potenciales usando stop loss y calculando el tamaño de posición según tu capital disponible. Nunca arriesgues más del 1-2% de tu cuenta por operación."

Si excedes 2 párrafos, estás violando el modo Rápida.
"""
        else:  # 'deep'
            mode_instruction = """

═══════════════════════════════════════════════════════════════
MODO: ESTUDIO PROFUNDO (OBLIGATORIO - RESPETA ESTO ESTRICTAMENTE)
═══════════════════════════════════════════════════════════════

RESPUESTA MÍNIMA: 5+ PÁRRAFOS O MÁS. DESARROLLA COMPLETAMENTE.

REGLAS ESTRICTAS:
- Mínimo 5 párrafos, preferiblemente más
- Primero: RESUMEN en 3-5 viñetas con las ideas clave
- Después: DESARROLLO COMPLETO con secciones y subtítulos (usa ##, ###)
- Incluye ejemplos prácticos y casos de uso
- Explica conceptos relacionados y contexto
- Estructura con: Introducción → Desarrollo → Ejemplos → Conclusiones
- Sé exhaustivo pero claro
- Usa markdown para organizar: encabezados, listas, negritas

EJEMPLO DE ESTRUCTURA:
## Resumen de Ideas Clave
- Idea 1
- Idea 2
- Idea 3

## Desarrollo Completo

### Subtema 1
[Párrafo 1: Explicación detallada...]
[Párrafo 2: Ejemplos y casos...]

### Subtema 2
[Párrafo 3: Más detalles...]
[Párrafo 4: Aplicaciones prácticas...]

### Subtema 3
[Párrafo 5: Conclusiones y recomendaciones...]

Si tienes menos de 5 párrafos, estás violando el modo Estudio Profundo.
"""
        
        # Construir el system_prompt según si es saludo o no
        if is_greeting:
            # Para saludos: system prompt simple y directo, SIN modo de respuesta
            system_prompt = """Eres CODEX TRADER, un asistente de IA especializado en trading.

INSTRUCCIONES PARA SALUDOS:
- Responde SOLO con 1-2 frases muy cortas
- Saluda amablemente
- Menciona brevemente en qué puedes ayudar (trading, gestión de riesgo, psicología, estrategias)
- Termina con una pregunta breve invitando al usuario a formular su duda
- NO uses encabezados, ni listas, ni markdown
- NO des explicaciones largas

Ejemplo: "¡Hola! Soy Codex Trader, tu asistente de IA especializado en trading. Puedo ayudarte con gestión de riesgo, análisis técnico, psicología del trader y diseño de estrategias. ¿Sobre qué tema de trading te gustaría que empecemos?"

Responde siempre en español."""
            # Para saludos, limitar tokens a 100 para forzar respuestas cortas
            max_tokens = 100
        else:
            # Para preguntas normales: system prompt completo con modo de respuesta
            system_prompt = config.ASSISTANT_DESCRIPTION + '\n\n' + greetings_instruction + '\n\n' + mode_instruction
            # Ajustar max_tokens según el modo
            if response_mode == 'fast':
                max_tokens = 300  # Limitar tokens para forzar respuestas cortas (1-2 párrafos)
            else:  # 'deep'
                max_tokens = 4000  # Más tokens para respuestas largas (5+ párrafos)
        
        # Preparar parámetros para LiteLLM
        litellm_params = {
            "model": chat_model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": config.MODEL_TEMPERATURE,
            "max_tokens": max_tokens
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
        
        # IMPORTANTE: Registrar uso del modelo para monitoreo de costos
        # Esta llamada es no-bloqueante y no afecta el flujo principal si falla
        try:
            from lib.model_usage import log_model_usage_from_response
            log_model_usage_from_response(
                user_id=str(user_id),
                model=chat_model,
                tokens_input=input_tokens,
                tokens_output=output_tokens
            )
        except Exception as e:
            # No es crítico si falla el logging, solo registrar el error
            print(f"WARNING: Error al registrar uso de modelo (no critico): {e}")
        
        # Loggear información detallada de tokens y costos
        print("=" * 60)
        print(f"[INFO] Consulta procesada:")
        print(f"  Modelo: {chat_model}")
        print(f"  Input tokens: {input_tokens}")
        print(f"  Output tokens: {output_tokens}")
        print(f"  Total tokens: {total_tokens_usados}")
        print(f"  Tokens restantes antes: {tokens_restantes}")
        print("=" * 60)
        
        # Guardar log de tokens en archivo para consulta posterior
        try:
            from datetime import datetime
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "user_id": str(user_id),
                "model": chat_model,
                "query_preview": query_input.query[:50] + "..." if len(query_input.query) > 50 else query_input.query,
                "response_mode": response_mode,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens_usados,
                "tokens_antes": tokens_restantes,
                "tokens_despues": nuevos_tokens
            }
            
            # Guardar en archivo JSON (append)
            import json
            log_file = "tokens_log.json"
            log_data = []
            
            # Leer logs existentes si el archivo existe
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        log_data = json.load(f)
                except:
                    log_data = []
            
            # Agregar nuevo log (mantener solo los últimos 100)
            log_data.append(log_entry)
            if len(log_data) > 100:
                log_data = log_data[-100:]
            
            # Guardar
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            # Si falla el logging, no es crítico, solo imprimir error
            print(f"⚠ No se pudo guardar log de tokens: {e}")
        
        # Usar total_tokens_usados para el descuento (mantener compatibilidad)
        tokens_usados = total_tokens_usados
        
        # Paso B: Descontar tokens de la base de datos y verificar uso justo
        nuevos_tokens = tokens_restantes - tokens_usados
        
        # IMPORTANTE: Lógica de uso justo (Fair Use)
        # Obtener información del perfil para calcular porcentaje de uso
        # Manejar el caso cuando las columnas no existen (compatibilidad con esquemas antiguos)
        update_data = {
            "tokens_restantes": nuevos_tokens
        }
        
        try:
            profile_fair_use = supabase_client.table("profiles").select(
                "tokens_monthly_limit, fair_use_warning_shown, fair_use_discount_eligible, fair_use_discount_used"
            ).eq("id", user_id).execute()
            
            if profile_fair_use.data:
                profile = profile_fair_use.data[0]
                tokens_monthly_limit = profile.get("tokens_monthly_limit") or 0
                
                if tokens_monthly_limit > 0:
                    # Calcular porcentaje de uso
                    tokens_usados_total = tokens_monthly_limit - nuevos_tokens
                    usage_percent = (tokens_usados_total / tokens_monthly_limit) * 100
                    
                    # Aviso suave al 80% de uso
                    if usage_percent >= 80 and not profile.get("fair_use_warning_shown", False):
                        update_data["fair_use_warning_shown"] = True
                        print(f"WARNING: Usuario {user_id} alcanzo 80% de uso ({usage_percent:.1f}%)")
                    
                    # Elegibilidad para descuento al 90% de uso
                    if usage_percent >= 90 and not profile.get("fair_use_discount_eligible", False):
                        from datetime import datetime
                        update_data["fair_use_discount_eligible"] = True
                        update_data["fair_use_discount_eligible_at"] = datetime.utcnow().isoformat()
                        print(f"🔔 Usuario {user_id} alcanzó 90% de uso ({usage_percent:.1f}%) - Elegible para descuento del 20%")
        except Exception as e:
            # Si las columnas no existen, continuar sin la lógica de uso justo
            logger.warning(f"Columnas de uso justo no disponibles (puede que no estén creadas): {e}")
            # Continuar sin actualizar campos de uso justo
        
        try:
            supabase_client.table("profiles").update(update_data).eq("id", user_id).execute()
            print(f"[INFO] Tokens descontados: {tokens_usados} tokens")
            print(f"[INFO] Tokens restantes después: {nuevos_tokens} tokens")
        except Exception as e:
            # Si falla la actualización, aún devolvemos la respuesta pero registramos el error
            print(f"ERROR: Error al actualizar tokens: {str(e)}")
        
        # Paso C: Crear o usar sesión de chat y guardar mensajes
        conversation_id = query_input.conversation_id
        try:
            # Si no hay conversation_id, crear una nueva sesión
            if not conversation_id:
                # Crear nueva sesión de chat
                session_response = supabase_client.table("chat_sessions").insert({
                    "user_id": user_id,
                    "title": query_input.query[:50] if len(query_input.query) > 50 else query_input.query
                }).execute()
                
                if session_response.data and len(session_response.data) > 0:
                    conversation_id = session_response.data[0]["id"]
                    print(f"[INFO] Nueva sesión de chat creada: {conversation_id}")
                else:
                    print(f"[WARN] No se pudo crear sesión de chat, continuando sin guardar historial")
            else:
                # Si hay conversation_id, verificar que existe y pertenece al usuario
                try:
                    session_check = supabase_client.table("chat_sessions").select("id").eq("id", conversation_id).eq("user_id", user_id).execute()
                    if not session_check.data:
                        # La sesión no existe o no pertenece al usuario, crear una nueva
                        print(f"[WARN] Sesión {conversation_id} no encontrada o no pertenece al usuario, creando nueva sesión")
                        session_response = supabase_client.table("chat_sessions").insert({
                            "user_id": user_id,
                            "title": query_input.query[:50] if len(query_input.query) > 50 else query_input.query
                        }).execute()
                        if session_response.data and len(session_response.data) > 0:
                            conversation_id = session_response.data[0]["id"]
                except Exception as e:
                    print(f"[WARN] Error verificando sesión: {e}, creando nueva sesión")
                    session_response = supabase_client.table("chat_sessions").insert({
                        "user_id": user_id,
                        "title": query_input.query[:50] if len(query_input.query) > 50 else query_input.query
                    }).execute()
                    if session_response.data and len(session_response.data) > 0:
                        conversation_id = session_response.data[0]["id"]
            
            # Guardar mensajes si tenemos conversation_id
            if conversation_id:
                # Guardar mensaje del usuario
                supabase_client.table("conversations").insert({
                    "user_id": user_id,
                    "conversation_id": conversation_id,
                    "message_role": "user",
                    "message_content": query_input.query,
                    "tokens_used": 0
                }).execute()
                
                # Guardar respuesta del asistente
                supabase_client.table("conversations").insert({
                    "user_id": user_id,
                    "conversation_id": conversation_id,
                    "message_role": "assistant",
                    "message_content": respuesta_texto,
                    "tokens_used": tokens_usados
                }).execute()
                
                # Actualizar updated_at de la sesión (se hace automáticamente con el trigger, pero lo hacemos explícitamente también)
                supabase_client.table("chat_sessions").update({
                    "updated_at": "now()"
                }).eq("id", conversation_id).execute()
        except Exception as e:
            # Si la tabla no existe o hay error, continuar sin guardar historial
            print(f"[WARN] No se pudo guardar historial (puede que la tabla no exista aún): {str(e)}")
            import traceback
            traceback.print_exc()
        
        # Devolver la respuesta con información de tokens y conversation_id
        return {
            "response": respuesta_texto,
            "tokens_usados": tokens_usados,
            "tokens_restantes": nuevos_tokens,
            "conversation_id": conversation_id
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
            "chat_sessions": "/chat-sessions (GET) - Lista de sesiones de chat",
            "chat_sessions_messages": "/chat-sessions/{id}/messages (GET) - Mensajes de una sesión",
            "create_chat_session": "/chat-sessions (POST) - Crear nueva sesión",
            "delete_chat_session": "/chat-sessions/{id} (DELETE) - Eliminar sesión",
            "update_chat_session": "/chat-sessions/{id} (PATCH) - Actualizar título",
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

# Endpoint para obtener lista de sesiones de chat
@app.get("/chat-sessions")
async def get_chat_sessions(user = Depends(get_user), limit: int = 50):
    """
    Endpoint para obtener la lista de sesiones de chat del usuario autenticado.
    Devuelve las sesiones ordenadas por fecha de actualización (más recientes primero).
    """
    try:
        user_id = user.id
        
        # Obtener sesiones de chat ordenadas por fecha de actualización (más recientes primero)
        sessions_response = supabase_client.table("chat_sessions").select(
            "id, title, created_at, updated_at"
        ).eq("user_id", user_id).order("updated_at", desc=True).limit(limit).execute()
        
        if not sessions_response.data:
            return {
                "sessions": [],
                "total": 0
            }
        
        return {
            "sessions": sessions_response.data,
            "total": len(sessions_response.data)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener sesiones de chat: {str(e)}"
        )

# Endpoint para obtener mensajes de una conversación específica
@app.get("/chat-sessions/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: str, user = Depends(get_user), limit: int = 100):
    """
    Endpoint para obtener los mensajes de una conversación específica.
    """
    try:
        user_id = user.id
        
        # Verificar que la conversación pertenezca al usuario
        session_check = supabase_client.table("chat_sessions").select("id").eq("id", conversation_id).eq("user_id", user_id).execute()
        if not session_check.data:
            raise HTTPException(
                status_code=404,
                detail="Conversación no encontrada o no pertenece al usuario"
            )
        
        # Obtener mensajes de la conversación ordenados por fecha de creación
        messages_response = supabase_client.table("conversations").select(
            "id, message_role, message_content, tokens_used, created_at"
        ).eq("conversation_id", conversation_id).eq("user_id", user_id).order("created_at", desc=False).limit(limit).execute()
        
        if not messages_response.data:
            return {
                "messages": [],
                "total": 0
            }
        
        return {
            "messages": messages_response.data,
            "total": len(messages_response.data)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener mensajes: {str(e)}"
        )

# Modelo para crear nueva conversación
class CreateChatSessionInput(BaseModel):
    title: Optional[str] = None

# Endpoint para crear una nueva conversación
@app.post("/chat-sessions")
async def create_chat_session(create_input: Optional[CreateChatSessionInput] = None, user = Depends(get_user)):
    """
    Endpoint para crear una nueva sesión de chat.
    """
    try:
        user_id = user.id
        
        # Crear nueva sesión de chat
        new_session = supabase_client.table("chat_sessions").insert({
            "user_id": user_id,
            "title": create_input.title if create_input and create_input.title else "Nueva conversación"
        }).execute()
        
        if not new_session.data:
            raise HTTPException(
                status_code=500,
                detail="Error al crear nueva conversación"
            )
        
        return {
            "session": new_session.data[0],
            "message": "Conversación creada exitosamente"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear conversación: {str(e)}"
        )

# ============================================================================
# ENDPOINTS DE BILLING / STRIPE
# ============================================================================

# Modelo para crear checkout session
class CheckoutSessionInput(BaseModel):
    planCode: str  # 'explorer', 'trader', 'pro', 'institucional'

# Endpoint para crear una sesión de checkout de Stripe
# RUTA: POST /billing/create-checkout-session
# ARCHIVO: main.py (línea ~1050)
@app.post("/billing/create-checkout-session")
async def create_checkout_session(
    checkout_input: CheckoutSessionInput,
    user = Depends(get_user)
):
    """
    Crea una sesión de checkout de Stripe para suscripciones.
    
    Recibe:
    - planCode: Código del plan ('explorer', 'trader', 'pro', 'institucional')
    
    Retorna:
    - url: URL de la sesión de checkout de Stripe para redirigir al usuario
    
    TODO: Asociar la sesión con el usuario logueado:
    - Agregar metadata a la Checkout Session con userId y email del usuario
    - Esto permitirá identificar al usuario cuando Stripe envíe el webhook
    """
    if not STRIPE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Stripe no está configurado. Verifica las variables de entorno STRIPE_SECRET_KEY y los Price IDs."
        )
    
    try:
        plan_code = checkout_input.planCode.lower()
        
        # Validar que el código de plan sea válido
        if not is_valid_plan_code(plan_code):
            raise HTTPException(
                status_code=400,
                detail=f"Código de plan inválido: {plan_code}. Debe ser uno de: explorer, trader, pro, institucional"
            )
        
        # Obtener el Price ID de Stripe para el plan
        price_id = get_stripe_price_id(plan_code)
        if not price_id:
            raise HTTPException(
                status_code=500,
                detail=f"Price ID no configurado para el plan: {plan_code}. Verifica STRIPE_PRICE_ID_{plan_code.upper()} en .env"
            )
        
        # Obtener userId y email del usuario autenticado
        user_id = user.id
        user_email = user.email
        
        # IMPORTANTE: Verificar elegibilidad para descuento de uso justo (Fair Use)
        # Si el usuario es elegible y aún no ha usado el descuento, aplicar cupón automáticamente
        discounts = None
        from lib.stripe import STRIPE_FAIR_USE_COUPON_ID
        
        if STRIPE_FAIR_USE_COUPON_ID:
            try:
                # Intentar obtener información del perfil del usuario con columnas de fair use
                profile_response = supabase_client.table("profiles").select(
                    "fair_use_discount_eligible, fair_use_discount_used"
                ).eq("id", user_id).execute()
                
                if profile_response.data:
                    profile = profile_response.data[0]
                    fair_use_eligible = profile.get("fair_use_discount_eligible", False)
                    fair_use_used = profile.get("fair_use_discount_used", False)
                    
                    # Aplicar cupón si es elegible y aún no lo ha usado
                    if fair_use_eligible and not fair_use_used:
                        discounts = [{"coupon": STRIPE_FAIR_USE_COUPON_ID}]
                        logger.info(f"✅ Aplicando cupón de uso justo (20% OFF) para usuario {user_id}")
            except Exception as e:
                # Si las columnas no existen, simplemente no aplicar descuento
                error_msg = str(e)
                if "does not exist" in error_msg or "42703" in error_msg:
                    logger.warning(f"⚠️ Columnas de fair use no disponibles, omitiendo descuento: {error_msg[:100]}")
                else:
                    logger.warning(f"⚠️ Error al verificar elegibilidad de fair use: {error_msg[:100]}")
                # Continuar sin descuento
        
        metadata = {
            "user_id": user_id,
            "user_email": user_email,
            "plan_code": plan_code
        }
        
        # Si se aplicó descuento, agregarlo a metadata para tracking
        if discounts:
            metadata["fair_use_discount_applied"] = "true"
        
        # Crear la sesión de checkout de Stripe
        checkout_session_params = {
            "mode": "subscription",
            "line_items": [
                {
                    "price": price_id,
                    "quantity": 1,
                }
            ],
            "success_url": f"{FRONTEND_URL}/app?checkout=success",
            "cancel_url": f"{FRONTEND_URL}/planes?checkout=cancel",
            "metadata": metadata,
            "customer_email": user_email,  # Pre-llenar el email del usuario
        }
        
        # Agregar descuentos solo si el usuario es elegible
        if discounts:
            checkout_session_params["discounts"] = discounts
        
        checkout_session = stripe.checkout.Session.create(**checkout_session_params)
        
        return {
            "url": checkout_session.url,
            "session_id": checkout_session.id
        }
        
    except HTTPException:
        raise
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error de Stripe: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear sesión de checkout: {str(e)}"
        )

# Endpoint para recibir webhooks de Stripe
# RUTA: POST /billing/stripe-webhook
# ARCHIVO: main.py (línea ~1135)
# IMPORTANTE: Este endpoint NO requiere autenticación normal, Stripe lo firma con webhook_secret
@app.post("/billing/stripe-webhook")
async def stripe_webhook(request: Request):
    """
    Endpoint para recibir y procesar webhooks de Stripe.
    
    Eventos manejados:
    - checkout.session.completed: Cuando un usuario completa el checkout
    - invoice.paid: Cuando se paga una factura (renovación mensual)
    
    Este endpoint actualiza en la base de datos:
    - stripe_customer_id: ID del cliente en Stripe
    - current_plan: Código del plan actual (explorer, trader, pro, institucional)
    - current_period_end: Fecha de fin del período actual de suscripción
    - tokens_restantes: Saldo de tokens basado en el plan
    
    NOTA: El frontend puede leer estos campos desde /app/billing o en el chat
    para mostrar el plan actual y el saldo de tokens.
    """
    if not STRIPE_AVAILABLE or not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=503,
            detail="Stripe webhooks no están configurados. Verifica STRIPE_WEBHOOK_SECRET en .env"
        )
    
    try:
        # Obtener el payload y la firma del webhook
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")
        
        if not sig_header:
            raise HTTPException(
                status_code=400,
                detail="Falta el header stripe-signature"
            )
        
        # Verificar la firma del webhook
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            # Payload inválido
            raise HTTPException(
                status_code=400,
                detail=f"Payload inválido: {str(e)}"
            )
        except stripe.error.SignatureVerificationError as e:
            # Firma inválida
            raise HTTPException(
                status_code=400,
                detail=f"Firma de webhook inválida: {str(e)}"
            )
        
        # Procesar el evento según su tipo
        event_type = event["type"]
        event_data = event["data"]["object"]
        
        if event_type == "checkout.session.completed":
            await handle_checkout_session_completed(event_data)
        elif event_type == "invoice.paid":
            await handle_invoice_paid(event_data)
        else:
            # Evento no manejado, pero retornamos 200 para que Stripe no lo reintente
            print(f"⚠️ Evento de Stripe no manejado: {event_type}")
        
        return {"status": "success"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error al procesar webhook de Stripe: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar webhook: {str(e)}"
        )


async def handle_checkout_session_completed(session: dict):
    """
    Maneja el evento checkout.session.completed de Stripe.
    
    Actualiza en la base de datos:
    - stripe_customer_id: ID del cliente en Stripe
    - current_plan: Plan seleccionado desde metadata
    - current_period_end: Fecha de expiración de la suscripción
    
    IMPORTANTE: Este es el lugar donde se actualiza current_plan y stripe_customer_id
    después de que un usuario completa el checkout.
    """
    try:
        # Extraer información de la sesión
        customer_id = session.get("customer")
        subscription_id = session.get("subscription")
        metadata = session.get("metadata", {})
        user_id = metadata.get("user_id")
        plan_code = metadata.get("plan_code")
        
        if not user_id:
            print(f"⚠️ checkout.session.completed sin user_id en metadata: {session.get('id')}")
            return
        
        if not customer_id:
            print(f"⚠️ checkout.session.completed sin customer_id: {session.get('id')}")
            return
        
        # Obtener información de la suscripción para current_period_end
        current_period_end = None
        if subscription_id:
            try:
                subscription = stripe.Subscription.retrieve(subscription_id)
                current_period_end = subscription.current_period_end
            except Exception as e:
                print(f"⚠️ Error al obtener suscripción {subscription_id}: {str(e)}")
        
        # Obtener información del plan para establecer tokens iniciales
        tokens_per_month = None
        if plan_code:
            from plans import get_plan_by_code
            plan = get_plan_by_code(plan_code)
            if plan:
                tokens_per_month = plan.tokens_per_month
        
        # Preparar datos para actualizar
        # IMPORTANTE: Aquí se actualiza current_plan, stripe_customer_id y tokens en la tabla profiles
        # El frontend puede leer estos valores desde /app/billing o en el chat
        update_data = {
            "stripe_customer_id": customer_id,
        }
        
        if plan_code:
            update_data["current_plan"] = plan_code
            # Establecer tokens iniciales y límite mensual según el plan
            if tokens_per_month:
                update_data["tokens_restantes"] = tokens_per_month
                # Intentar actualizar tokens_monthly_limit solo si la columna existe
                try:
                    update_data["tokens_monthly_limit"] = tokens_per_month
                    # Resetear campos de uso justo al suscribirse por primera vez
                    update_data["fair_use_warning_shown"] = False
                    update_data["fair_use_discount_eligible"] = False
                    update_data["fair_use_discount_used"] = False
                    update_data["fair_use_discount_eligible_at"] = None
                except Exception as e:
                    logger.warning(f"No se pudo actualizar tokens_monthly_limit (columna puede no existir): {e}")
        
        # IMPORTANTE: Si el usuario usó el descuento de uso justo, marcarlo
        # Verificar en metadata si se aplicó el descuento
        if metadata.get("fair_use_discount_applied") == "true":
            # Verificar que el usuario tenía elegibilidad antes de marcar como usado
            profile_check = supabase_client.table("profiles").select(
                "fair_use_discount_eligible"
            ).eq("id", user_id).execute()
            
            if profile_check.data and profile_check.data[0].get("fair_use_discount_eligible", False):
                update_data["fair_use_discount_used"] = True
                print(f"✅ Descuento de uso justo marcado como usado para usuario {user_id}")
        
        if current_period_end:
            # Convertir timestamp de Unix a datetime ISO
            from datetime import datetime
            update_data["current_period_end"] = datetime.fromtimestamp(current_period_end).isoformat()
        
        # Actualizar el perfil del usuario
        update_response = supabase_client.table("profiles").update(update_data).eq("id", user_id).execute()
        
        if update_response.data:
            print(f"✅ Perfil actualizado para usuario {user_id}: plan={plan_code}, customer={customer_id}")
            
            # IMPORTANTE: Registrar pago inicial en tabla stripe_payments para análisis de ingresos
            try:
                from datetime import datetime
                # Obtener monto desde Stripe (necesitamos obtener la invoice o subscription)
                amount_usd = None
                payment_date = None
                
                if subscription_id:
                    try:
                        subscription = stripe.Subscription.retrieve(subscription_id)
                        # Obtener la última invoice pagada
                        if subscription.latest_invoice:
                            invoice_obj = stripe.Invoice.retrieve(subscription.latest_invoice)
                            amount_usd = invoice_obj.amount_paid / 100.0 if invoice_obj.amount_paid else None
                            payment_date = datetime.fromtimestamp(invoice_obj.created).isoformat() if invoice_obj.created else None
                    except Exception as e:
                        print(f"⚠️ Error al obtener invoice desde subscription: {e}")
                
                # Si no se pudo obtener desde subscription, usar precio del plan
                if amount_usd is None and plan_code:
                    from plans import get_plan_by_code
                    plan = get_plan_by_code(plan_code)
                    if plan:
                        amount_usd = plan.price_usd
                        payment_date = datetime.utcnow().isoformat()
                
                # Insertar en tabla de pagos si tenemos los datos
                if amount_usd is not None:
                    payment_data = {
                        "invoice_id": f"checkout-{session.get('id', 'unknown')}",
                        "customer_id": customer_id,
                        "user_id": user_id,
                        "plan_code": plan_code,
                        "amount_usd": amount_usd,
                        "currency": "usd",
                        "payment_date": payment_date or datetime.utcnow().isoformat()
                    }
                    
                    try:
                        payment_response = supabase_client.table("stripe_payments").insert(payment_data).execute()
                        if payment_response.data:
                            print(f"✅ Pago inicial registrado: ${amount_usd:.2f} USD para usuario {user_id} (plan: {plan_code})")
                    except Exception as insert_error:
                        # Si ya existe, no es crítico
                        print(f"⚠️ Pago ya registrado o error al insertar: {insert_error}")
            except Exception as payment_error:
                # No es crítico si falla el registro de pago
                print(f"⚠️ Error al registrar pago inicial (no crítico): {payment_error}")
        else:
            print(f"⚠️ No se encontró perfil para usuario {user_id}")
            
    except Exception as e:
        print(f"❌ Error en handle_checkout_session_completed: {str(e)}")
        raise


async def handle_invoice_paid(invoice: dict):
    """
    Maneja el evento invoice.paid de Stripe (renovación mensual).
    
    Actualiza en la base de datos:
    - current_plan: Plan determinado desde el price_id de la invoice
    - tokens_restantes: Tokens del mes basados en el plan
    - current_period_end: Fecha de fin del período de facturación
    
    IMPORTANTE: Este es el lugar donde se actualiza tokens_restantes cada mes
    cuando se renueva la suscripción. El frontend puede leer este valor
    desde /app/billing o en el chat para mostrar el saldo actual.
    """
    try:
        # Extraer información de la invoice
        customer_id = invoice.get("customer")
        subscription_id = invoice.get("subscription")
        
        if not customer_id:
            print(f"⚠️ invoice.paid sin customer_id: {invoice.get('id')}")
            return
        
        # Buscar el usuario por stripe_customer_id (obtener también email y plan anterior)
        profile_response = supabase_client.table("profiles").select("id, email, current_plan").eq("stripe_customer_id", customer_id).execute()
        
        if not profile_response.data:
            print(f"⚠️ No se encontró usuario con stripe_customer_id: {customer_id}")
            return
        
        user_id = profile_response.data[0]["id"]
        user_email = profile_response.data[0].get("email", "")
        previous_plan = profile_response.data[0].get("current_plan")
        
        # Determinar si es nueva suscripción o renovación
        is_new_subscription = previous_plan is None or previous_plan == ""
        event_type = "nueva suscripción" if is_new_subscription else "renovación"
        
        # Obtener el price_id de la invoice para determinar el plan
        line_items = invoice.get("lines", {}).get("data", [])
        if not line_items:
            print(f"⚠️ invoice.paid sin line_items: {invoice.get('id')}")
            return
        
        # El primer line_item debería tener el price del plan
        price_id = line_items[0].get("price", {}).get("id")
        if not price_id:
            print(f"⚠️ invoice.paid sin price_id en line_items: {invoice.get('id')}")
            return
        
        # Determinar el plan desde el price_id
        plan_code = get_plan_code_from_price_id(price_id)
        if not plan_code:
            print(f"⚠️ No se encontró plan para price_id: {price_id}")
            return
        
        # Obtener información del plan para calcular tokens
        from plans import get_plan_by_code
        plan = get_plan_by_code(plan_code)
        if not plan:
            print(f"⚠️ No se encontró plan con código: {plan_code}")
            return
        
        tokens_per_month = plan.tokens_per_month
        
        # Obtener current_period_end desde la invoice
        period_end = None
        if line_items[0].get("period"):
            period_end_timestamp = line_items[0]["period"].get("end")
            if period_end_timestamp:
                from datetime import datetime
                period_end = datetime.fromtimestamp(period_end_timestamp).isoformat()
        
        # IMPORTANTE: Resetear campos de uso justo al renovar suscripción
        # Esto se hace cada vez que se paga una invoice (renovación mensual)
        # El frontend puede leer estos valores desde GET /me/usage
        update_data = {
            "current_plan": plan_code,
            "tokens_restantes": tokens_per_month  # Resetear tokens al renovar suscripción
        }
        
        # Intentar actualizar tokens_monthly_limit solo si la columna existe
        try:
            update_data["tokens_monthly_limit"] = tokens_per_month
            update_data["fair_use_warning_shown"] = False  # Resetear aviso suave
            update_data["fair_use_discount_eligible"] = False  # Resetear elegibilidad para descuento
            update_data["fair_use_discount_used"] = False  # Resetear uso de descuento
            update_data["fair_use_discount_eligible_at"] = None  # Resetear fecha de elegibilidad
        except Exception as e:
            logger.warning(f"No se pudo actualizar campos de uso justo (columnas pueden no existir): {e}")
        
        if period_end:
            update_data["current_period_end"] = period_end
        
        # IMPORTANTE: Lógica de recompensas de referidos
        # Verificar si este es el primer pago del usuario (para dar recompensa al que invita)
        invoice_id = invoice.get("id")
        process_referral_reward = False
        
        if invoice_id:
            # Verificar si ya se procesó esta recompensa (idempotencia)
            reward_event_check = supabase_client.table("referral_reward_events").select("id").eq("invoice_id", invoice_id).execute()
            
            if not reward_event_check.data:
                # Esta invoice no ha sido procesada antes, verificar si es primera suscripción
                profile_check = supabase_client.table("profiles").select(
                    "referred_by_user_id, has_generated_referral_reward"
                ).eq("id", user_id).execute()
                
                if profile_check.data:
                    referred_by_id = profile_check.data[0].get("referred_by_user_id")
                    has_generated_reward = profile_check.data[0].get("has_generated_referral_reward", False)
                    
                    # Si fue referido y aún no ha generado recompensa, procesar
                    if referred_by_id and not has_generated_reward:
                        process_referral_reward = True
        
        # Si es el primer pago, marcar que ya generó recompensa
        if process_referral_reward:
            update_data["has_generated_referral_reward"] = True
        
        # Actualizar el perfil del usuario
        update_response = supabase_client.table("profiles").update(update_data).eq("id", user_id).execute()
        
        if update_response.data:
            print(f"✅ Suscripción renovada para usuario {user_id}: plan={plan_code}, tokens={tokens_per_month}")
            
            # IMPORTANTE: Registrar pago en tabla stripe_payments para análisis de ingresos
            try:
                from datetime import datetime
                
                # Obtener monto de la invoice
                amount_total = invoice.get("amount_paid", invoice.get("amount_due", 0))
                amount_usd = amount_total / 100.0  # Stripe usa centavos
                currency = invoice.get("currency", "usd").upper()
                
                # Obtener fecha del pago
                payment_date = None
                if invoice.get("status_transitions", {}).get("paid_at"):
                    payment_date = invoice["status_transitions"]["paid_at"]
                elif invoice.get("created"):
                    payment_date = invoice["created"]
                
                # Convertir timestamp a datetime ISO si es necesario
                if payment_date and isinstance(payment_date, (int, float)):
                    payment_date = datetime.fromtimestamp(payment_date).isoformat()
                
                # Insertar en tabla de pagos (con manejo de duplicados)
                payment_data = {
                    "invoice_id": invoice_id,
                    "customer_id": customer_id,
                    "user_id": user_id,
                    "plan_code": plan_code,
                    "amount_usd": amount_usd,
                    "currency": currency,
                    "payment_date": payment_date or datetime.utcnow().isoformat()
                }
                
                # Intentar insertar (puede fallar si ya existe por el UNIQUE constraint)
                try:
                    payment_response = supabase_client.table("stripe_payments").insert(payment_data).execute()
                    if payment_response.data:
                        print(f"✅ Pago registrado: ${amount_usd:.2f} USD para usuario {user_id} (plan: {plan_code})")
                except Exception as insert_error:
                    # Si ya existe, actualizar en lugar de insertar
                    try:
                        supabase_client.table("stripe_payments").update({
                            "amount_usd": amount_usd,
                            "plan_code": plan_code,
                            "payment_date": payment_date or datetime.utcnow().isoformat()
                        }).eq("invoice_id", invoice_id).execute()
                        print(f"✅ Pago actualizado: ${amount_usd:.2f} USD para invoice {invoice_id}")
                    except Exception as update_error:
                        print(f"⚠️ No se pudo registrar/actualizar pago: {update_error}")
            except Exception as payment_error:
                # No es crítico si falla el registro de pago
                print(f"⚠️ Error al registrar pago (no crítico): {payment_error}")
            
            # Procesar recompensa al que invita (si aplica)
            if process_referral_reward:
                await process_referrer_reward(user_id, referred_by_id, invoice_id)
            
            # IMPORTANTE: Enviar emails de notificación (admin y usuario)
            # Esto se hace en segundo plano y no bloquea el procesamiento del webhook
            try:
                from lib.email import send_admin_email, send_email
                from datetime import datetime
                import threading
                
                # Obtener información adicional para los emails
                plan_name = plan.name
                # Obtener monto de la invoice (ya se calculó arriba, pero lo recalculamos aquí para seguridad)
                amount_total = invoice.get("amount_paid", invoice.get("amount_due", 0))
                amount_usd = amount_total / 100.0  # Stripe usa centavos
                
                # Formatear fecha de pago (obtener directamente desde invoice)
                payment_date_str = None
                if invoice.get("status_transitions", {}).get("paid_at"):
                    payment_date_str = datetime.fromtimestamp(invoice["status_transitions"]["paid_at"]).strftime('%Y-%m-%d %H:%M:%S')
                elif invoice.get("created"):
                    payment_date_str = datetime.fromtimestamp(invoice["created"]).strftime('%Y-%m-%d %H:%M:%S')
                else:
                    payment_date_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                
                # Formatear fecha de próxima renovación
                next_renewal_str = "N/A"
                if period_end:
                    try:
                        if isinstance(period_end, str):
                            if "T" in period_end:
                                dt = datetime.fromisoformat(period_end.replace("Z", "+00:00"))
                            else:
                                dt = datetime.fromisoformat(period_end)
                        else:
                            dt = period_end
                        next_renewal_str = dt.strftime('%d/%m/%Y')
                    except:
                        next_renewal_str = str(period_end)
                
                # 1) EMAIL AL ADMIN: Notificación de pago
                def send_admin_email_background():
                    try:
                        admin_html = f"""
                        <html>
                        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                            <h2 style="color: #2563eb;">Nuevo pago en Codex Trader</h2>
                            <p>Se ha procesado un pago de suscripción en Codex Trader.</p>
                            <ul>
                                <li><strong>Email del usuario:</strong> {user_email}</li>
                                <li><strong>ID de usuario:</strong> {user_id}</li>
                                <li><strong>Plan:</strong> {plan_name} ({plan_code})</li>
                                <li><strong>Monto:</strong> ${amount_usd:.2f} USD</li>
                                <li><strong>Fecha del pago:</strong> {payment_date_str}</li>
                                <li><strong>Tipo de evento:</strong> {event_type}</li>
                                <li><strong>Invoice ID:</strong> {invoice_id}</li>
                            </ul>
                        </body>
                        </html>
                        """
                        send_admin_email("Nuevo pago en Codex Trader", admin_html)
                    except Exception as e:
                        print(f"WARNING: Error al enviar email al admin: {e}")
                
                # 2) EMAIL AL USUARIO: Confirmación de activación/renovación
                def send_user_email_background():
                    try:
                        if user_email:
                            user_html = f"""
                            <html>
                            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                                <h2 style="color: #2563eb;">Tu plan {plan_name} en Codex Trader está activo</h2>
                                <p>Hola {user_email.split('@')[0] if '@' in user_email else 'usuario'},</p>
                                <p>Tu plan <strong>{plan_name}</strong> en Codex Trader ha sido {'activado' if is_new_subscription else 'renovado'} correctamente.</p>
                                
                                <h3 style="color: #2563eb; margin-top: 20px;">Resumen:</h3>
                                <ul>
                                    <li><strong>Plan:</strong> {plan_name}</li>
                                    <li><strong>Precio:</strong> ${amount_usd:.2f} USD</li>
                                    <li><strong>Tokens disponibles este mes:</strong> {tokens_per_month:,}</li>
                                    <li><strong>Próxima renovación:</strong> {next_renewal_str}</li>
                                </ul>
                                
                                <h3 style="color: #2563eb; margin-top: 20px;">Recuerda:</h3>
                                <ul>
                                    <li>Puedes ver tu uso de tokens en el panel de cuenta.</li>
                                    <li>Tienes acceso al modelo de IA especializado en trading y tu biblioteca profesional.</li>
                                </ul>
                                
                                <p style="margin-top: 30px; color: #666; font-size: 12px;">
                                    Si no reconoces este pago, contáctanos respondiendo a este correo.
                                </p>
                            </body>
                            </html>
                            """
                            send_email(
                                to=user_email,
                                subject=f"Tu plan {plan_name} en Codex Trader está activo",
                                html=user_html
                            )
                    except Exception as e:
                        print(f"WARNING: Error al enviar email al usuario: {e}")
                
                # Enviar emails en background (no bloquea)
                admin_thread = threading.Thread(target=send_admin_email_background, daemon=True)
                admin_thread.start()
                
                user_thread = threading.Thread(target=send_user_email_background, daemon=True)
                user_thread.start()
                
            except Exception as email_error:
                # No es crítico si falla el envío de emails
                print(f"WARNING: Error al enviar emails de notificación (no crítico): {email_error}")
        else:
            print(f"⚠️ No se pudo actualizar perfil para usuario {user_id}")
            
    except Exception as e:
        print(f"❌ Error en handle_invoice_paid: {str(e)}")
        raise


async def process_referrer_reward(user_id: str, referrer_id: str, invoice_id: str):
    """
    Procesa la recompensa de 10,000 tokens para el usuario que invitó.
    
    IMPORTANTE: Esta función es idempotente y verifica:
    - Que el referrer no haya alcanzado el límite de 5 recompensas
    - Que esta invoice no haya sido procesada antes
    
    Args:
        user_id: ID del usuario que pagó (invitado)
        referrer_id: ID del usuario que invitó
        invoice_id: ID de la invoice de Stripe (para idempotencia)
    """
    try:
        # Obtener información del referrer
        referrer_response = supabase_client.table("profiles").select(
            "id, referral_rewards_count, tokens_restantes"
        ).eq("id", referrer_id).execute()
        
        if not referrer_response.data:
            print(f"⚠️ No se encontró referrer con ID: {referrer_id}")
            return
        
        referrer = referrer_response.data[0]
        rewards_count = referrer.get("referral_rewards_count", 0)
        
        # Verificar límite de 5 recompensas
        if rewards_count >= 5:
            print(f"ℹ️ Referrer {referrer_id} ya alcanzó el límite de 5 recompensas")
            return
        
        # Verificar idempotencia: esta invoice no debe haber sido procesada
        reward_event_check = supabase_client.table("referral_reward_events").select("id").eq("invoice_id", invoice_id).execute()
        if reward_event_check.data:
            print(f"ℹ️ Recompensa para invoice {invoice_id} ya fue procesada (idempotencia)")
            return
        
        # Recompensa: 10,000 tokens
        reward_amount = 10000
        
        # Sumar tokens al referrer
        current_tokens = referrer.get("tokens_restantes", 0) or 0
        new_tokens = current_tokens + reward_amount
        
        # Actualizar referrer: tokens, contador y tokens ganados
        update_response = supabase_client.table("profiles").update({
            "tokens_restantes": new_tokens,
            "referral_rewards_count": rewards_count + 1,
            "referral_tokens_earned": referrer.get("referral_tokens_earned", 0) + reward_amount
        }).eq("id", referrer_id).execute()
        
        if update_response.data:
            # Registrar evento para idempotencia
            event_response = supabase_client.table("referral_reward_events").insert({
                "invoice_id": invoice_id,
                "user_id": user_id,
                "referrer_id": referrer_id,
                "reward_type": "first_payment",
                "tokens_granted": reward_amount
            }).execute()
            
            if event_response.data:
                print(f"✅ Recompensa otorgada: {reward_amount:,} tokens a referrer {referrer_id} por invitado {user_id} (invoice: {invoice_id})")
            else:
                print(f"⚠️ Recompensa otorgada pero no se pudo registrar evento para invoice {invoice_id}")
        else:
            print(f"⚠️ No se pudo actualizar referrer {referrer_id}")
            
    except Exception as e:
        print(f"❌ Error al procesar recompensa de referrer: {str(e)}")
        # No lanzar excepción para no romper el webhook principal

# ============================================================================
# FUNCIONES UTILITARIAS DE TOKENS Y RECOMPENSAS
# ============================================================================

def add_tokens_to_user(user_id: str, amount: int, reason: str = "Bonus") -> bool:
    """
    Suma tokens a un usuario de forma segura.
    
    Esta función es idempotente y puede usarse para:
    - Bonus de referidos
    - Descuentos
    - Campañas
    - Cualquier otro tipo de recompensa
    
    Args:
        user_id: ID del usuario
        amount: Cantidad de tokens a sumar (puede ser negativo para restar)
        reason: Razón del cambio (para logging)
        
    Returns:
        True si se actualizó correctamente, False en caso contrario
    """
    try:
        # Obtener tokens actuales
        profile_response = supabase_client.table("profiles").select("tokens_restantes").eq("id", user_id).execute()
        
        if not profile_response.data:
            print(f"⚠️ No se encontró perfil para usuario {user_id}")
            return False
        
        current_tokens = profile_response.data[0]["tokens_restantes"] or 0
        new_tokens = current_tokens + amount
        
        # Actualizar tokens
        update_response = supabase_client.table("profiles").update({
            "tokens_restantes": new_tokens
        }).eq("id", user_id).execute()
        
        if update_response.data:
            print(f"✅ Tokens actualizados para usuario {user_id}: {current_tokens} + {amount} = {new_tokens} ({reason})")
            return True
        else:
            print(f"⚠️ No se pudo actualizar tokens para usuario {user_id}")
            return False
            
    except Exception as e:
        print(f"❌ Error al sumar tokens a usuario {user_id}: {str(e)}")
        return False

# ============================================================================
# ENDPOINTS DE USO JUSTO (FAIR USE)
# ============================================================================

# Endpoint para obtener información de uso del usuario actual
# RUTA: GET /me/usage
# ARCHIVO: main.py (línea ~1545)
@app.get("/me/usage")
async def get_user_usage(user = Depends(get_user)):
    """
    Obtiene información sobre el uso de tokens y estado de uso justo del usuario.
    
    Retorna:
    - tokens_monthly_limit: Límite mensual de tokens según el plan
    - tokens_restantes: Tokens restantes actuales
    - usage_percent: Porcentaje de uso (0-100)
    - fair_use_warning_shown: Si se mostró aviso suave al 80%
    - fair_use_discount_eligible: Si es elegible para descuento al 90%
    - fair_use_discount_used: Si ya usó el descuento en este ciclo
    
    IMPORTANTE: El frontend puede usar esta información para mostrar:
    - Estado de uso en el chat
    - Avisos de uso justo
    - Elegibilidad para descuento del 20% en la página de billing
    """
    try:
        user_id = user.id
        
        # Intentar obtener columnas de uso justo, pero manejar si no existen
        try:
            profile_response = supabase_client.table("profiles").select(
                "tokens_restantes, tokens_monthly_limit, current_plan, fair_use_warning_shown, "
                "fair_use_discount_eligible, fair_use_discount_used, fair_use_discount_eligible_at"
            ).eq("id", user_id).execute()
        except Exception as e:
            # Si falla por columnas faltantes, intentar solo con columnas básicas
            logger.warning(f"Error al obtener columnas de uso justo, intentando solo columnas básicas: {e}")
            profile_response = supabase_client.table("profiles").select(
                "tokens_restantes, current_plan"
            ).eq("id", user_id).execute()
        
        if not profile_response.data:
            raise HTTPException(
                status_code=404,
                detail="Perfil de usuario no encontrado"
            )
        
        profile = profile_response.data[0]
        tokens_restantes = profile.get("tokens_restantes", 0) or 0
        tokens_monthly_limit = profile.get("tokens_monthly_limit", 0) or 0
        
        # Calcular porcentaje de uso solo si tokens_monthly_limit existe
        usage_percent = 0.0
        tokens_usados = 0
        if tokens_monthly_limit > 0:
            tokens_usados = tokens_monthly_limit - tokens_restantes
            usage_percent = (tokens_usados / tokens_monthly_limit) * 100
            # Asegurar que no sea negativo
            usage_percent = max(0.0, min(100.0, usage_percent))
        
        result = {
            "tokens_restantes": tokens_restantes,
            "current_plan": profile.get("current_plan")
        }
        
        # Agregar campos de uso justo solo si existen
        if tokens_monthly_limit > 0:
            result["tokens_monthly_limit"] = tokens_monthly_limit
            result["tokens_usados"] = tokens_usados
            result["usage_percent"] = usage_percent
        
        # Intentar agregar campos de fair use si existen
        if "fair_use_warning_shown" in profile:
            result["fair_use_warning_shown"] = profile.get("fair_use_warning_shown", False)
        if "fair_use_discount_eligible" in profile:
            result["fair_use_discount_eligible"] = profile.get("fair_use_discount_eligible", False)
        if "fair_use_discount_used" in profile:
            result["fair_use_discount_used"] = profile.get("fair_use_discount_used", False)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener información de uso: {str(e)}"
        )

# ============================================================================
# FUNCIONES DE ADMINISTRACIÓN
# ============================================================================

# TODO: Implementar un sistema de roles más robusto
# Por ahora, usamos una lista de emails de administradores
# En producción, deberías usar un sistema de roles en la base de datos
ADMIN_EMAILS = [
    # Agrega aquí los emails de los administradores
    # Ejemplo: "admin@codextrader.mx"
]

def is_admin_user(user) -> bool:
    """
    Verifica si un usuario es administrador.
    
    TODO: Implementar un sistema de roles más robusto:
    - Agregar campo 'role' o 'is_admin' a la tabla profiles
    - O crear una tabla de roles separada
    - Por ahora, usa una lista de emails en ADMIN_EMAILS
    
    Args:
        user: Objeto usuario de Supabase
        
    Returns:
        True si el usuario es admin, False en caso contrario
    """
    if not user or not user.email:
        return False
    
    # Verificar si el email está en la lista de admins
    if user.email.lower() in [email.lower() for email in ADMIN_EMAILS]:
        return True
    
    # TODO: Verificar en la base de datos si el usuario tiene rol de admin
    # Ejemplo:
    # profile = supabase_client.table("profiles").select("is_admin").eq("id", user.id).execute()
    # return profile.data[0].get("is_admin", False) if profile.data else False
    
    return False

# ============================================================================
# ENDPOINTS DE ADMINISTRACIÓN
# ============================================================================

# Endpoint para obtener resumen de costos e ingresos
# RUTA: GET /admin/cost-summary?from=YYYY-MM-DD&to=YYYY-MM-DD
# ARCHIVO: main.py (línea ~1800)
# IMPORTANTE: Este endpoint es solo para administradores
@app.get("/admin/cost-summary")
async def get_cost_summary(
    from_date: str = Query(..., description="Fecha de inicio (YYYY-MM-DD)"),
    to_date: str = Query(..., description="Fecha de fin (YYYY-MM-DD)"),
    user = Depends(get_user)
):
    """
    Obtiene un resumen de costos e ingresos para el rango de fechas especificado.
    
    IMPORTANTE: Este endpoint es solo para administradores.
    Verifica que el usuario tenga permisos de administrador antes de procesar.
    
    Retorna:
    - from: Fecha de inicio
    - to: Fecha de fin
    - daily: Array con resumen diario (costos e ingresos por día)
    - totals: Totales agregados (costos, ingresos, margen)
    
    TODO: Implementar sistema de roles más robusto para verificar permisos de admin
    """
    # Verificar que el usuario es administrador
    if not is_admin_user(user):
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado. Este endpoint es solo para administradores."
        )
    
    try:
        from datetime import datetime, timedelta
        try:
            import pytz
        except ImportError:
            # Si pytz no está disponible, usar timezone de datetime
            from datetime import timezone
            pytz = None
        
        # Parsear fechas
        try:
            date_from = datetime.strptime(from_date, "%Y-%m-%d")
            date_to = datetime.strptime(to_date, "%Y-%m-%d")
            # Ajustar a inicio y fin del día
            date_from = date_from.replace(hour=0, minute=0, second=0, microsecond=0)
            date_to = date_to.replace(hour=23, minute=59, second=59, microsecond=999999)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Formato de fecha inválido. Use YYYY-MM-DD"
            )
        
        # Validar rango de fechas
        if date_from > date_to:
            raise HTTPException(
                status_code=400,
                detail="La fecha de inicio debe ser anterior a la fecha de fin"
            )
        
        # Convertir a UTC para consultas
        if pytz:
            utc = pytz.UTC
            date_from_utc = date_from.replace(tzinfo=utc)
            date_to_utc = date_to.replace(tzinfo=utc)
        else:
            from datetime import timezone
            utc = timezone.utc
            date_from_utc = date_from.replace(tzinfo=utc)
            date_to_utc = date_to.replace(tzinfo=utc)
        
        # Consultar costos de modelos agrupados por día
        usage_response = supabase_client.table("model_usage_events").select(
            "tokens_input, tokens_output, cost_estimated_usd, created_at"
        ).gte("created_at", date_from_utc.isoformat()).lte("created_at", date_to_utc.isoformat()).execute()
        
        # Agrupar costos por día
        daily_costs = {}
        total_tokens_input = 0
        total_tokens_output = 0
        total_cost_usd = 0.0
        
        if usage_response.data:
            for event in usage_response.data:
                created_at = event.get("created_at")
                if created_at:
                    # Extraer fecha (sin hora)
                    event_date = created_at.split("T")[0] if "T" in created_at else created_at.split(" ")[0]
                    
                    if event_date not in daily_costs:
                        daily_costs[event_date] = {
                            "tokens_input": 0,
                            "tokens_output": 0,
                            "cost_estimated_usd": 0.0
                        }
                    
                    daily_costs[event_date]["tokens_input"] += event.get("tokens_input", 0)
                    daily_costs[event_date]["tokens_output"] += event.get("tokens_output", 0)
                    daily_costs[event_date]["cost_estimated_usd"] += float(event.get("cost_estimated_usd", 0))
                    
                    total_tokens_input += event.get("tokens_input", 0)
                    total_tokens_output += event.get("tokens_output", 0)
                    total_cost_usd += float(event.get("cost_estimated_usd", 0))
        
        # Consultar ingresos de Stripe agrupados por día
        payments_response = supabase_client.table("stripe_payments").select(
            "amount_usd, payment_date"
        ).gte("payment_date", date_from_utc.isoformat()).lte("payment_date", date_to_utc.isoformat()).execute()
        
        # Agrupar ingresos por día
        daily_revenue = {}
        total_revenue_usd = 0.0
        
        if payments_response.data:
            for payment in payments_response.data:
                payment_date_str = payment.get("payment_date")
                if payment_date_str:
                    # Extraer fecha (sin hora)
                    payment_date = payment_date_str.split("T")[0] if "T" in payment_date_str else payment_date_str.split(" ")[0]
                    
                    if payment_date not in daily_revenue:
                        daily_revenue[payment_date] = 0.0
                    
                    amount = float(payment.get("amount_usd", 0))
                    daily_revenue[payment_date] += amount
                    total_revenue_usd += amount
        
        # Combinar datos diarios
        daily_summary = []
        current_date = date_from.date()
        end_date = date_to.date()
        
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            
            costs = daily_costs.get(date_str, {
                "tokens_input": 0,
                "tokens_output": 0,
                "cost_estimated_usd": 0.0
            })
            
            revenue = daily_revenue.get(date_str, 0.0)
            
            daily_summary.append({
                "date": date_str,
                "tokens_input": costs["tokens_input"],
                "tokens_output": costs["tokens_output"],
                "cost_estimated_usd": round(costs["cost_estimated_usd"], 6),
                "revenue_usd": round(revenue, 2)
            })
            
            current_date += timedelta(days=1)
        
        # Calcular margen
        margin_usd = total_revenue_usd - total_cost_usd
        
        return {
            "from": from_date,
            "to": to_date,
            "daily": daily_summary,
            "totals": {
                "tokens_input": total_tokens_input,
                "tokens_output": total_tokens_output,
                "cost_estimated_usd": round(total_cost_usd, 6),
                "revenue_usd": round(total_revenue_usd, 2),
                "margin_usd": round(margin_usd, 2),
                "margin_percent": round((margin_usd / total_revenue_usd * 100) if total_revenue_usd > 0 else 0, 2)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener resumen de costos: {str(e)}"
        )

# ============================================================================
# ENDPOINTS DE DEBUG (SOLO PARA DESARROLLO)
# ============================================================================

# TODO: DESACTIVAR O PROTEGER ESTE ENDPOINT EN PRODUCCIÓN
# Este endpoint es solo para pruebas de email durante el desarrollo.
# En producción, deberías:
# - Desactivarlo completamente, o
# - Protegerlo con autenticación de administrador, o
# - Restringirlo solo a ciertos IPs

class TestEmailInput(BaseModel):
    """Modelo para el endpoint de prueba de email"""
    to: Optional[str] = None

@app.get("/debug/test-email")
async def test_email_get(to: Optional[str] = None):
    """
    Endpoint GET temporal SOLO PARA PRUEBAS de envío de emails.
    
    IMPORTANTE: Este endpoint es solo para desarrollo.
    TODO: Desactivar o proteger con auth en producción.
    
    Query params (opcional):
        ?to=email@ejemplo.com  // Opcional, usa ADMIN_EMAIL si no se proporciona
    
    Returns:
        JSON con success: true si no hubo error aparente
    """
    try:
        from lib.email import send_email, ADMIN_EMAIL
        
        # Determinar destinatario
        recipient = to if to else ADMIN_EMAIL
        
        if not recipient:
            return {
                "success": False,
                "error": "No se proporciono destinatario y ADMIN_EMAIL no esta configurado"
            }
        
        # Enviar email de prueba
        subject = "Prueba SMTP Codex"
        html_content = "<p>Este es un correo de prueba desde el backend de Codex Trader.</p>"
        
        # El envío se hace síncronamente pero no bloquea el servidor si falla
        # Si falla, send_email registra el error pero no lanza excepción
        result = send_email(
            to=recipient,
            subject=subject,
            html=html_content
        )
        
        if result:
            return {
                "success": True,
                "message": f"Email de prueba enviado a {recipient}",
                "recipient": recipient
            }
        else:
            return {
                "success": False,
                "error": "Error al enviar email (revisa los logs del servidor para mas detalles)",
                "recipient": recipient
            }
            
    except Exception as e:
        # Capturar cualquier error inesperado
        print(f"ERROR: Error inesperado en test-email: {e}")
        return {
            "success": False,
            "error": f"Error inesperado: {str(e)}"
        }

@app.post("/debug/test-email")
async def test_email_post(input_data: Optional[TestEmailInput] = None):
    """
    Endpoint temporal SOLO PARA PRUEBAS de envío de emails.
    
    IMPORTANTE: Este endpoint es solo para desarrollo.
    TODO: Desactivar o proteger con auth en producción.
    
    Body (opcional):
        {
            "to": "email@ejemplo.com"  // Opcional, usa ADMIN_EMAIL si no se proporciona
        }
    
    Returns:
        JSON con success: true si no hubo error aparente
    """
    try:
        from lib.email import send_email, ADMIN_EMAIL
        
        # Determinar destinatario
        recipient = None
        if input_data and input_data.to:
            recipient = input_data.to
        else:
            recipient = ADMIN_EMAIL
        
        if not recipient:
            return {
                "success": False,
                "error": "No se proporcionó destinatario y ADMIN_EMAIL no está configurado"
            }
        
        # Enviar email de prueba
        subject = "Prueba SMTP Codex"
        html_content = "<p>Este es un correo de prueba desde el backend de Codex Trader.</p>"
        
        # El envío se hace síncronamente pero no bloquea el servidor si falla
        # Si falla, send_email registra el error pero no lanza excepción
        result = send_email(
            to=recipient,
            subject=subject,
            html=html_content
        )
        
        if result:
            return {
                "success": True,
                "message": f"Email de prueba enviado a {recipient}"
            }
        else:
            return {
                "success": False,
                "error": "Error al enviar email (revisa los logs del servidor para más detalles)"
            }
            
    except Exception as e:
        # Capturar cualquier error inesperado
        print(f"ERROR: Error inesperado en test-email: {e}")
        return {
            "success": False,
            "error": f"Error inesperado: {str(e)}"
        }

# ============================================================================
# ENDPOINTS DE USUARIOS
# ============================================================================

# Endpoint para notificar registro de nuevo usuario
# RUTA: POST /users/notify-registration
# ARCHIVO: main.py (línea ~2025)
# IMPORTANTE: Este endpoint debe llamarse desde el frontend después del registro
# También puede llamarse con un token_hash de confirmación en el body
class NotifyRegistrationInput(BaseModel):
    token_hash: Optional[str] = None

@app.post("/users/notify-registration")
async def notify_user_registration(
    input_data: Optional[NotifyRegistrationInput] = None,
    authorization: Optional[str] = Header(None)
):
    """
    Notifica al administrador sobre un nuevo registro de usuario.
    
    Este endpoint debe llamarse desde el frontend después de que un usuario
    se registra exitosamente. Envía un email al administrador con la información
    del nuevo usuario.
    
    Puede llamarse de dos formas:
    1. Con token de autenticación en el header (usuario ya logueado)
    2. Con token_hash de confirmación en el body (después de confirmar email)
    
    IMPORTANTE: El envío de email se hace en segundo plano y no bloquea la respuesta.
    """
    from datetime import datetime
    logger.info("=" * 60)
    logger.info("[API] POST /users/notify-registration recibido")
    logger.info(f"   Authorization header presente: {bool(authorization)}")
    logger.info(f"   Token_hash en body: {bool(input_data and input_data.token_hash)}")
    logger.info(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[API] POST /users/notify-registration recibido")
    print(f"   Authorization header presente: {bool(authorization)}")
    print(f"   Token_hash en body: {bool(input_data and input_data.token_hash)}")
    print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        user = None
        
        # Intentar obtener usuario desde el token de autenticación
        if authorization:
            try:
                logger.info("[DEBUG] Intentando obtener usuario desde token de autenticación...")
                logger.info(f"[DEBUG] Token (primeros 20 chars): {authorization[:20] if authorization else 'None'}...")
                print(f"   [DEBUG] Intentando obtener usuario desde token de autenticación...")
                print(f"   [DEBUG] Token (primeros 20 chars): {authorization[:20] if authorization else 'None'}...")
                user = await get_user(authorization)
                logger.info(f"[OK] Usuario obtenido desde token: {user.email if user else 'None'}")
                logger.info(f"[DEBUG] User ID: {user.id if user else 'None'}")
                print(f"   [OK] Usuario obtenido desde token: {user.email if user else 'None'}")
                print(f"   [DEBUG] User ID: {user.id if user else 'None'}")
            except HTTPException as e:
                logger.warning(f"[WARNING] Error al obtener usuario desde token: {e.detail}")
                logger.warning(f"[DEBUG] Status code: {e.status_code}")
                print(f"   [WARNING] Error al obtener usuario desde token: {e.detail}")
                print(f"   [DEBUG] Status code: {e.status_code}")
                # Si falla la autenticación, continuar para intentar con token_hash
                pass
            except Exception as e:
                logger.error(f"[ERROR] Excepción inesperada al obtener usuario: {e}", exc_info=True)
                print(f"   [ERROR] Excepción inesperada al obtener usuario: {e}")
                import traceback
                traceback.print_exc()
                pass
        
        # Si no hay usuario autenticado pero hay token_hash, verificar el token_hash
        if not user and input_data and input_data.token_hash:
            try:
                print(f"   Intentando verificar token_hash...")
                # Verificar el token_hash con Supabase
                verify_response = supabase_client.auth.verify_otp({
                    "type": "email",
                    "token_hash": input_data.token_hash
                })
                if verify_response.user:
                    user = verify_response.user
                    print(f"   [OK] Usuario obtenido desde token_hash: {user.email if user else 'None'}")
                else:
                    print(f"   [ERROR] Token_hash invalido: no se obtuvo usuario")
                    raise HTTPException(
                        status_code=401,
                        detail="Token de confirmación inválido"
                    )
            except Exception as e:
                print(f"   [ERROR] Error al verificar token_hash: {str(e)}")
                raise HTTPException(
                    status_code=401,
                    detail=f"Error al verificar token de confirmación: {str(e)}"
                )
        
        # Si aún no hay usuario, error
        if not user:
            print(f"   [ERROR] No se pudo obtener usuario. Authorization: {bool(authorization)}, Token_hash: {bool(input_data and input_data.token_hash)}")
            raise HTTPException(
                status_code=401,
                detail="Se requiere autenticación (header Authorization) o token_hash de confirmación en el body"
            )
        
        user_id = user.id
        user_email = user.email
        logger.info(f"[EMAIL] Procesando emails para usuario: {user_email} (ID: {user_id})")
        print(f"   [EMAIL] Procesando emails para usuario: {user_email} (ID: {user_id})")
        
        # PROTECCIÓN CONTRA DUPLICADOS: Verificar si ya se enviaron los emails de bienvenida
        # Usar un sistema de cache en memoria para evitar duplicados en la misma sesión
        # También verificar en la base de datos si existe un flag (opcional, se puede agregar después)
        import hashlib
        import time
        
        # Crear una clave única para este usuario en esta sesión
        cache_key = f"welcome_email_sent_{user_id}"
        
        # Cache simple en memoria (se puede mejorar con Redis en producción)
        if not hasattr(notify_user_registration, '_email_cache'):
            notify_user_registration._email_cache = {}
        
        # Limpiar cache antiguo (más de 1 hora)
        current_time = time.time()
        notify_user_registration._email_cache = {
            k: v for k, v in notify_user_registration._email_cache.items()
            if current_time - v < 3600  # 1 hora
        }
        
        # Verificar si ya se envió en los últimos 5 minutos
        if cache_key in notify_user_registration._email_cache:
            sent_time = notify_user_registration._email_cache[cache_key]
            time_since_sent = current_time - sent_time
            if time_since_sent < 300:  # 5 minutos
                logger.warning(f"[WARNING] Emails de bienvenida ya enviados recientemente para {user_email} (hace {int(time_since_sent)} segundos). Ignorando solicitud duplicada.")
                print(f"   [WARNING] Emails de bienvenida ya enviados recientemente. Ignorando solicitud duplicada.")
                return {
                    "success": True,
                    "message": "Emails ya fueron enviados anteriormente",
                    "already_sent": True
                }
        
        # Importar constantes de negocio y helpers de referidos
        from lib.business import (
            INITIAL_FREE_TOKENS,
            REF_INVITED_BONUS_TOKENS,
            REF_REFERRER_BONUS_TOKENS,
            REF_MAX_REWARDS,
            APP_NAME
        )
        from lib.referrals import assign_referral_code_if_needed, build_referral_url
        
        # IMPORTANTE: Asignar referral_code ANTES de obtener el perfil y enviar emails
        logger.info(f"[REFERRALS] Verificando/asignando referral_code para usuario {user_id}...")
        referral_code = assign_referral_code_if_needed(supabase_client, user_id)
        
        if not referral_code:
            logger.error(f"[REFERRALS] ERROR: No se pudo asignar referral_code al usuario {user_id}")
            # Intentar obtener el código del perfil como fallback
            try:
                profile_check = supabase_client.table("profiles").select("referral_code").eq("id", user_id).execute()
                if profile_check.data and profile_check.data[0].get("referral_code"):
                    referral_code = profile_check.data[0]["referral_code"]
                    logger.info(f"[REFERRALS] Código encontrado en perfil: {referral_code}")
                else:
                    referral_code = "No disponible"
                    logger.warning(f"[REFERRALS] Usuario {user_id} no tiene referral_code y no se pudo generar")
            except Exception as e:
                logger.error(f"[REFERRALS] Error al verificar código en perfil: {e}")
                referral_code = "No disponible"
        
        # Construir referral_url usando FRONTEND_URL
        referral_url = build_referral_url(referral_code)
        logger.info(f"[REFERRALS] Referral URL construida: {referral_url}")
        
        # Obtener información del perfil del usuario
        # Intentar obtener todas las columnas disponibles, manejando errores si alguna no existe
        try:
            # Primero intentar obtener todas las columnas (incluyendo referral_code si existe)
            profile_response = supabase_client.table("profiles").select(
                "referral_code, referred_by_user_id, current_plan, created_at, tokens_restantes"
            ).eq("id", user_id).execute()
        except Exception as e:
            # Si falla porque referral_code no existe, intentar sin esa columna
            logger.warning(f"[WARNING] Error al obtener perfil con referral_code, intentando sin esa columna: {e}")
            try:
                profile_response = supabase_client.table("profiles").select(
                    "referred_by_user_id, current_plan, created_at, tokens_restantes"
                ).eq("id", user_id).execute()
            except Exception as e2:
                logger.error(f"[ERROR] Error al obtener perfil: {e2}")
                profile_response = None
        
        if not profile_response or not profile_response.data:
            # Si no hay perfil, el usuario acaba de registrarse
            # El perfil se creará automáticamente por el trigger
            profile_data = {}
        else:
            profile_data = profile_response.data[0]
        
        # Asegurar que tenemos el referral_code (usar el que acabamos de asignar o el del perfil)
        if not referral_code or referral_code == "No disponible":
            referral_code = profile_data.get("referral_code") or referral_code or "No disponible"
        
        # Si aún no hay código, intentar asignarlo una vez más
        if not referral_code or referral_code == "No disponible":
            logger.warning(f"[REFERRALS] Reintentando asignar código...")
            referral_code = assign_referral_code_if_needed(supabase_client, user_id)
            if referral_code:
                referral_url = build_referral_url(referral_code)
                logger.info(f"[REFERRALS] Código asignado en segundo intento: {referral_code}")
        
        referred_by_id = profile_data.get("referred_by_user_id")
        current_plan = profile_data.get("current_plan")
        if not current_plan:
            current_plan = "Sin plan (modo prueba)"
        created_at = profile_data.get("created_at")
        initial_tokens = profile_data.get("tokens_restantes", INITIAL_FREE_TOKENS)
        
        # Obtener información del referrer si existe
        referrer_info = "No aplica"
        if referred_by_id:
            try:
                referrer_response = supabase_client.table("profiles").select("email").eq("id", referred_by_id).execute()
                if referrer_response.data:
                    referrer_info = f"{referrer_response.data[0].get('email', 'N/A')} (ID: {referred_by_id})"
                else:
                    referrer_info = f"ID: {referred_by_id}"
            except Exception:
                referrer_info = f"ID: {referred_by_id}"
        
        # IMPORTANTE: Enviar email de notificación al admin
        # Esto se hace en segundo plano y no bloquea la respuesta
        try:
            from lib.email import send_admin_email
            from datetime import datetime
            
            # Formatear fecha
            try:
                if created_at:
                    if isinstance(created_at, str):
                        if "T" in created_at:
                            date_obj = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                        else:
                            date_obj = datetime.fromisoformat(created_at)
                        formatted_date = date_obj.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        formatted_date = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                else:
                    formatted_date = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                formatted_date = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%); padding: 20px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h2 style="color: white; margin: 0; font-size: 24px;">Nuevo registro en Codex Trader</h2>
                </div>
                
                <div style="background: #ffffff; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <p style="font-size: 16px; margin-bottom: 20px;">
                        Se ha registrado un nuevo usuario en Codex Trader.
                    </p>
                    
                    <div style="background: #f9fafb; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <ul style="list-style: none; padding: 0; margin: 0;">
                            <li style="margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid #e5e7eb;">
                                <strong style="color: #2563eb;">Email:</strong> 
                                <span style="color: #333;">{user_email}</span>
                            </li>
                            <li style="margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid #e5e7eb;">
                                <strong style="color: #2563eb;">ID de usuario:</strong> 
                                <span style="color: #333; font-family: monospace; font-size: 12px;">{user_id}</span>
                            </li>
                            <li style="margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid #e5e7eb;">
                                <strong style="color: #2563eb;">Fecha de registro:</strong> 
                                <span style="color: #333;">{formatted_date}</span>
                            </li>
                            <li style="margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid #e5e7eb;">
                                <strong style="color: #2563eb;">Plan actual:</strong> 
                                <span style="color: #333;">{current_plan}</span>
                            </li>
                            <li style="margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid #e5e7eb;">
                                <strong style="color: #2563eb;">Tokens iniciales asignados:</strong> 
                                <span style="color: #333;">{INITIAL_FREE_TOKENS:,} tokens</span>
                            </li>
                            <li style="margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid #e5e7eb;">
                                <strong style="color: #2563eb;">Código de referido:</strong> 
                                <span style="color: #333; font-family: monospace; font-weight: bold;">{referral_code if referral_code and referral_code != "No disponible" else "No disponible (error al generar)"}</span>
                            </li>
                            <li style="margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid #e5e7eb;">
                                <strong style="color: #2563eb;">Enlace de invitación:</strong> 
                                <span style="color: #333; font-size: 12px; word-break: break-all;">
                                    <a href="{referral_url}" style="color: #2563eb; text-decoration: none;">{referral_url}</a>
                                </span>
                            </li>
                            <li style="margin-bottom: 0;">
                                <strong style="color: #2563eb;">Registrado por referido:</strong> 
                                <span style="color: #333;">{referrer_info}</span>
                            </li>
                        </ul>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Enviar email en segundo plano (no bloquea)
            # IMPORTANTE: Enviar directamente en lugar de usar threads para evitar problemas
            # Los threads pueden no ejecutarse correctamente en algunos entornos
            print(f"   [EMAIL] Enviando email al admin...")
            try:
                result = send_admin_email("Nuevo registro en Codex Trader", html_content)
                if result:
                    print(f"   [OK] Email al admin enviado correctamente")
                else:
                    print(f"   [ERROR] Error al enviar email al admin (revisa logs anteriores)")
            except Exception as e:
                print(f"   [ERROR] ERROR al enviar email al admin: {e}")
                import traceback
                traceback.print_exc()
        except Exception as email_error:
            # No es crítico si falla el email
            print(f"   [WARNING] No se pudo enviar email de notificacion de registro: {email_error}")
        
        # IMPORTANTE: Enviar email de bienvenida al usuario
        # Esto se hace en segundo plano y no bloquea la respuesta
        try:
            from lib.email import send_email
            
            # Construir enlaces usando FRONTEND_URL
            base_url = FRONTEND_URL
            referral_url = f"{base_url}/registro?ref={referral_code}"
            app_url = f"{base_url}/app"
            
            # Obtener nombre del usuario desde el email (parte antes del @)
            user_name = user_email.split('@')[0] if '@' in user_email else 'usuario'
            
            welcome_html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.8; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1 style="color: white; margin: 0; font-size: 28px;">🧠📈 Bienvenido a Codex Trader</h1>
                </div>
                
                <div style="background: #ffffff; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <!-- Bloque: Tu cuenta -->
                    <div style="margin-bottom: 30px;">
                        <p style="font-size: 16px; margin-bottom: 20px;">
                            Hola <strong>{user_email}</strong>, bienvenido a Codex Trader.
                        </p>
                        
                        <div style="background: #f9fafb; padding: 20px; border-radius: 8px; border-left: 4px solid #2563eb;">
                            <ul style="list-style: none; padding: 0; margin: 0;">
                                <li style="margin-bottom: 10px; color: #333;">
                                    <strong>Plan actual:</strong> Modo prueba (sin suscripción)
                                </li>
                                <li style="margin-bottom: 10px; color: #333;">
                                    <strong>Tokens iniciales:</strong> {INITIAL_FREE_TOKENS:,} para probar el asistente
                                </li>
                                <li style="margin-bottom: 0; color: #333;">
                                    <strong>Acceso al asistente:</strong> 
                                    <a href="{app_url}" style="color: #2563eb; text-decoration: none; font-weight: bold;">Empieza aquí</a>
                                </li>
                            </ul>
                        </div>
                    </div>
                    
                    <!-- Bloque: ¿Qué puedes hacer con Codex? -->
                    <div style="background: #f0f9ff; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #2563eb;">
                        <h3 style="color: #2563eb; margin-top: 0; font-size: 18px;">¿Qué puedes hacer con Codex?</h3>
                        <ul style="margin: 10px 0; padding-left: 20px; color: #333;">
                            <li style="margin-bottom: 10px;">Pedir explicaciones claras sobre gestión de riesgo, tamaño de posición y drawdown.</li>
                            <li style="margin-bottom: 10px;">Profundizar en psicología del trader y disciplina.</li>
                            <li style="margin-bottom: 10px;">Analizar setups, ideas de estrategia y marcos temporales.</li>
                            <li style="margin-bottom: 0;">Usarlo como cerebro de estudio apoyado en contenido profesional de trading.</li>
                        </ul>
                    </div>
                    
                    <!-- Botón de llamada a la acción -->
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{app_url}" style="display: inline-block; background: #2563eb; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px;">
                            🚀 Empieza aquí
                        </a>
                    </div>
                    
                    <!-- Bloque: Invita a tus amigos y gana tokens -->
                    <div style="background: #fef3c7; padding: 20px; border-radius: 8px; margin: 30px 0; border-left: 4px solid #f59e0b;">
                        <h3 style="color: #92400e; margin-top: 0; font-size: 18px;">💎 Invita a tus amigos y gana tokens</h3>
                        <p style="margin-bottom: 15px; color: #78350f;">
                            Comparte tu enlace personal y ambos ganan:
                        </p>
                        <ul style="margin: 15px 0; padding-left: 20px; color: #78350f;">
                            <li style="margin-bottom: 10px;">
                                Tu amigo recibe <strong>+{REF_INVITED_BONUS_TOKENS:,} tokens de bienvenida</strong> cuando activa su primer plan de pago.
                            </li>
                            <li style="margin-bottom: 15px;">
                                Tú ganas <strong>+{REF_REFERRER_BONUS_TOKENS:,} tokens</strong> por cada amigo que pague su primer plan (hasta {REF_MAX_REWARDS} referidos con recompensa completa).
                            </li>
                        </ul>
                        <div style="background: white; padding: 15px; border-radius: 6px; margin: 15px 0; border: 2px dashed #d97706;">
                            <p style="margin: 5px 0; font-size: 14px; color: #666;"><strong>Tu código de referido:</strong></p>
                            <p style="margin: 5px 0; font-size: 18px; font-weight: bold; color: #2563eb; word-break: break-all; font-family: monospace;">{referral_code if referral_code and referral_code != "No disponible" else "Se generará en unos minutos"}</p>
                            <p style="margin: 10px 0 5px 0; font-size: 14px; color: #666;"><strong>Tu enlace de invitación:</strong></p>
                            <p style="margin: 5px 0; font-size: 14px; color: #2563eb; word-break: break-all;">
                                <a href="{referral_url}" style="color: #2563eb; text-decoration: none;">{referral_url}</a>
                            </p>
                        </div>
                    </div>
                    
                    <!-- Bloque final: Disclaimer -->
                    <p style="font-size: 12px; margin-top: 30px; color: #666; text-align: center; border-top: 1px solid #e5e7eb; padding-top: 20px; line-height: 1.6;">
                        Codex Trader es una herramienta educativa. No ofrecemos asesoría financiera personalizada ni recomendaciones directas de compra/venta. Los resultados pasados no garantizan rendimientos futuros. Cada cliente es responsable de sus decisiones en el mercado.
                    </p>
                </div>
            </body>
            </html>
            """
            
            # Enviar email de bienvenida directamente (síncrono para garantizar envío)
            logger.info("[EMAIL] ========================================")
            logger.info("[EMAIL] INICIANDO ENVIO DE EMAIL DE BIENVENIDA")
            logger.info("[EMAIL] ========================================")
            print(f"   [EMAIL] ========================================")
            print(f"   [EMAIL] INICIANDO ENVIO DE EMAIL DE BIENVENIDA")
            print(f"   [EMAIL] ========================================")
            logger.info(f"[EMAIL] Destinatario: {user_email}")
            print(f"   [EMAIL] Destinatario: {user_email}")
            logger.info(f"[EMAIL] Enviando email de bienvenida a {user_email}...")
            print(f"   [EMAIL] Enviando email de bienvenida a {user_email}...")
            try:
                result = send_email(
                    to=user_email,
                    subject="🧠📈 Bienvenido a Codex Trader",
                    html=welcome_html
                )
                logger.info(f"[EMAIL] Resultado de send_email: {result}")
                print(f"   [EMAIL] Resultado de send_email: {result}")
                if result:
                    logger.info(f"[OK] Email de bienvenida enviado correctamente a {user_email}")
                    print(f"   [OK] Email de bienvenida enviado correctamente a {user_email}")
                else:
                    logger.error("[ERROR] Error al enviar email de bienvenida (revisa logs anteriores)")
                    print(f"   [ERROR] Error al enviar email de bienvenida (revisa logs anteriores)")
                    print(f"   [ERROR] Verifica SMTP_AVAILABLE y configuración de email")
            except Exception as e:
                logger.error(f"[ERROR] ERROR al enviar email de bienvenida: {e}", exc_info=True)
                print(f"   [ERROR] ERROR al enviar email de bienvenida: {e}")
                import traceback
                traceback.print_exc()
            logger.info("[EMAIL] ========================================")
            print(f"   [EMAIL] ========================================")
        except Exception as welcome_error:
            # No es crítico si falla el email de bienvenida
            logger.warning(f"[WARNING] No se pudo enviar email de bienvenida (no critico): {welcome_error}")
            print(f"   [WARNING] No se pudo enviar email de bienvenida (no critico): {welcome_error}")
        
        # Marcar en cache que los emails fueron enviados (solo si llegamos aquí sin errores críticos)
        try:
            notify_user_registration._email_cache[cache_key] = time.time()
            logger.info(f"[OK] Emails enviados y marcados en cache para {user_email}")
        except:
            pass  # Si falla el cache, no es crítico
        
        logger.info("[OK] Endpoint completado exitosamente. Emails enviados directamente.")
        print(f"   [OK] Endpoint completado exitosamente. Emails enviados directamente.")
        return {
            "success": True,
            "message": "Registro notificado correctamente"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # No lanzar error, solo registrar
        logger.error("=" * 60)
        logger.error(f"[ERROR] ERROR en endpoint notify-registration: {str(e)}", exc_info=True)
        logger.error("=" * 60)
        print(f"   [ERROR] ERROR en endpoint notify-registration: {str(e)}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "message": "Error al notificar registro, pero el usuario fue creado correctamente"
        }

# ============================================================================
# ENDPOINTS DE REFERIDOS
# ============================================================================

# Endpoint para obtener resumen de estadísticas de referidos
# RUTA: GET /me/referrals-summary
# ARCHIVO: main.py (línea ~1695)
@app.get("/me/referrals-summary")
async def get_referrals_summary(user = Depends(get_user)):
    """
    Obtiene un resumen de estadísticas de referidos del usuario actual.
    
    Retorna:
    - totalInvited: Total de usuarios que se registraron con el código de referido
    - totalPaid: Total de usuarios que pagaron su primera suscripción
    - referralRewardsCount: Cantidad de referidos que ya generaron recompensa (máximo 5)
    - referralTokensEarned: Tokens totales ganados por referidos
    - referralCode: Código de referido del usuario
    """
    try:
        user_id = user.id
        
        # Obtener información del perfil del usuario
        profile_response = supabase_client.table("profiles").select(
            "referral_code, referral_rewards_count, referral_tokens_earned"
        ).eq("id", user_id).execute()
        
        if not profile_response.data:
            raise HTTPException(
                status_code=404,
                detail="Perfil de usuario no encontrado"
            )
        
        profile = profile_response.data[0]
        referral_code = profile.get("referral_code")
        referral_rewards_count = profile.get("referral_rewards_count", 0)
        referral_tokens_earned = profile.get("referral_tokens_earned", 0)
        
        # Contar total de usuarios que se registraron con este código de referido
        total_invited_response = supabase_client.table("profiles").select(
            "id"
        ).eq("referred_by_user_id", user_id).execute()
        
        total_invited = len(total_invited_response.data) if total_invited_response.data else 0
        
        # Contar usuarios que ya pagaron (tienen has_generated_referral_reward = true)
        total_paid_response = supabase_client.table("profiles").select(
            "id"
        ).eq("referred_by_user_id", user_id).eq("has_generated_referral_reward", True).execute()
        
        total_paid = len(total_paid_response.data) if total_paid_response.data else 0
        
        return {
            "totalInvited": total_invited,
            "totalPaid": total_paid,
            "referralRewardsCount": referral_rewards_count,
            "referralTokensEarned": referral_tokens_earned,
            "referralCode": referral_code
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener resumen de referidos: {str(e)}"
        )

# Modelo para procesar referido
class ProcessReferralInput(BaseModel):
    referral_code: str  # Código de referido del usuario que invitó

# Endpoint para procesar un código de referido después del registro
# RUTA: POST /referrals/process
# ARCHIVO: main.py (línea ~1370)
@app.post("/referrals/process")
async def process_referral(
    referral_input: ProcessReferralInput,
    user = Depends(get_user)
):
    """
    Procesa un código de referido después del registro de un usuario.
    
    Este endpoint debe llamarse después de que un usuario se registra con un código
    de referido (por ejemplo, desde ?ref=XXXX en la URL de registro).
    
    Recibe:
    - referral_code: Código de referido del usuario que invitó
    
    Actualiza:
    - referred_by_user_id: ID del usuario que invitó
    
    Retorna:
    - success: True si se procesó correctamente
    - message: Mensaje descriptivo
    """
    try:
        user_id = user.id
        referral_code = referral_input.referral_code.strip().upper()
        
        if not referral_code:
            raise HTTPException(
                status_code=400,
                detail="El código de referido no puede estar vacío"
            )
        
        # Verificar que el usuario no tenga ya un referido asignado
        profile_response = supabase_client.table("profiles").select("referred_by_user_id").eq("id", user_id).execute()
        
        if not profile_response.data:
            raise HTTPException(
                status_code=404,
                detail="Perfil de usuario no encontrado"
            )
        
        existing_referrer = profile_response.data[0].get("referred_by_user_id")
        if existing_referrer:
            raise HTTPException(
                status_code=400,
                detail="Este usuario ya tiene un referido asignado"
            )
        
        # Verificar que el usuario no se esté refiriendo a sí mismo
        user_profile = supabase_client.table("profiles").select("referral_code").eq("id", user_id).execute()
        if user_profile.data and user_profile.data[0].get("referral_code") == referral_code:
            raise HTTPException(
                status_code=400,
                detail="No puedes usar tu propio código de referido"
            )
        
        # Buscar al usuario que tiene ese código de referido
        referrer_response = supabase_client.table("profiles").select("id, email, referral_code").eq("referral_code", referral_code).execute()
        
        if not referrer_response.data:
            raise HTTPException(
                status_code=404,
                detail=f"Código de referido inválido: {referral_code}"
            )
        
        referrer_id = referrer_response.data[0]["id"]
        
        # Actualizar el perfil del usuario con referred_by_user_id
        update_response = supabase_client.table("profiles").update({
            "referred_by_user_id": referrer_id
        }).eq("id", user_id).execute()
        
        if update_response.data:
            # Aplicar bono de bienvenida de 5,000 tokens al usuario referido
            welcome_bonus = 5000
            add_tokens_to_user(user_id, welcome_bonus, "Bono de bienvenida por referido")
            
            # IMPORTANTE: Enviar email de notificación al admin sobre nuevo registro
            # Esto se hace en segundo plano y no bloquea la respuesta
            try:
                from lib.email import send_admin_email
                from datetime import datetime
                
                # Obtener información del usuario y referrer para el email
                user_email = user.email
                referrer_email = referrer_response.data[0].get('email', 'N/A')
                
                html_content = f"""
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <h2 style="color: #2563eb;">Nuevo registro en Codex Trader</h2>
                    <p>Se ha registrado un nuevo usuario en Codex Trader.</p>
                    <ul>
                        <li><strong>Email:</strong> {user_email}</li>
                        <li><strong>Fecha de registro:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</li>
                        <li><strong>Registrado por referido:</strong> {referrer_email} (ID: {referrer_id})</li>
                        <li><strong>Código de referido usado:</strong> {referral_code}</li>
                    </ul>
                </body>
                </html>
                """
                
                # Enviar email en segundo plano (no bloquea)
                # Usar threading para ejecutar en background
                import threading
                def send_email_background():
                    try:
                        send_admin_email("Nuevo registro en Codex Trader", html_content)
                    except Exception as e:
                        print(f"WARNING: Error al enviar email en background: {e}")
                
                email_thread = threading.Thread(target=send_email_background, daemon=True)
                email_thread.start()
            except Exception as email_error:
                # No es crítico si falla el email
                print(f"WARNING: No se pudo enviar email de notificación de registro: {email_error}")
            
            return {
                "success": True,
                "message": f"Referido procesado correctamente. Fuiste referido por {referrer_response.data[0].get('email', 'usuario')}. ¡Recibiste {welcome_bonus:,} tokens de bienvenida!",
                "referrer_id": referrer_id,
                "welcome_bonus": welcome_bonus
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Error al actualizar el perfil con el referido"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar referido: {str(e)}"
        )

# Endpoint para obtener información del referido del usuario actual
# RUTA: GET /referrals/info
# ARCHIVO: main.py (línea ~1450)
@app.get("/referrals/info")
async def get_referral_info(user = Depends(get_user)):
    """
    Obtiene información sobre el sistema de referidos del usuario actual.
    
    Retorna:
    - referral_code: Código de referido del usuario
    - referred_by_user_id: ID del usuario que lo invitó (si aplica)
    - referral_rewards_count: Cantidad de referidos que han generado recompensa
    - referral_tokens_earned: Tokens totales obtenidos por referidos
    """
    try:
        user_id = user.id
        
        profile_response = supabase_client.table("profiles").select(
            "referral_code, referred_by_user_id, referral_rewards_count, referral_tokens_earned"
        ).eq("id", user_id).execute()
        
        if not profile_response.data:
            raise HTTPException(
                status_code=404,
                detail="Perfil de usuario no encontrado"
            )
        
        profile = profile_response.data[0]
        
        return {
            "referral_code": profile.get("referral_code"),
            "referred_by_user_id": profile.get("referred_by_user_id"),
            "referral_rewards_count": profile.get("referral_rewards_count", 0),
            "referral_tokens_earned": profile.get("referral_tokens_earned", 0)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener información de referidos: {str(e)}"
        )

# ============================================================================
# ENDPOINTS DE CHAT SESSIONS
# ============================================================================

# Endpoint para eliminar una conversación
@app.delete("/chat-sessions/{conversation_id}")
async def delete_chat_session(conversation_id: str, user = Depends(get_user)):
    """
    Endpoint para eliminar una sesión de chat y todos sus mensajes.
    """
    try:
        user_id = user.id
        
        # Verificar que la conversación pertenezca al usuario
        session_check = supabase_client.table("chat_sessions").select("id").eq("id", conversation_id).eq("user_id", user_id).execute()
        if not session_check.data:
            raise HTTPException(
                status_code=404,
                detail="Conversación no encontrada o no pertenece al usuario"
            )
        
        # Eliminar la sesión (los mensajes se eliminarán automáticamente por CASCADE)
        supabase_client.table("chat_sessions").delete().eq("id", conversation_id).execute()
        
        return {
            "message": "Conversación eliminada exitosamente"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al eliminar conversación: {str(e)}"
        )

# Endpoint para actualizar el título de una conversación
@app.patch("/chat-sessions/{conversation_id}")
async def update_chat_session(conversation_id: str, title: str, user = Depends(get_user)):
    """
    Endpoint para actualizar el título de una sesión de chat.
    """
    try:
        user_id = user.id
        
        # Verificar que la conversación pertenezca al usuario
        session_check = supabase_client.table("chat_sessions").select("id").eq("id", conversation_id).eq("user_id", user_id).execute()
        if not session_check.data:
            raise HTTPException(
                status_code=404,
                detail="Conversación no encontrada o no pertenece al usuario"
            )
        
        # Actualizar el título
        updated_session = supabase_client.table("chat_sessions").update({
            "title": title,
            "updated_at": "now()"
        }).eq("id", conversation_id).execute()
        
        if not updated_session.data:
            raise HTTPException(
                status_code=500,
                detail="Error al actualizar conversación"
            )
        
        return {
            "session": updated_session.data[0],
            "message": "Título actualizado exitosamente"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al actualizar conversación: {str(e)}"
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
    
    # Railway y otras plataformas proporcionan PORT como variable de entorno
    # Si no está disponible, usar 8000 por defecto (desarrollo local)
    port = int(os.getenv("PORT", 8000))
    print(f"✓ Iniciando servidor en puerto {port}")
    
    # Importar webhook de nuevo usuario (solución alternativa)
    try:
        from webhook_new_user import create_webhook_endpoint
        create_webhook_endpoint(app, supabase_client)
        print("Webhook de nuevo usuario configurado correctamente")
    except Exception as e:
        print(f"WARNING: No se pudo configurar webhook de nuevo usuario: {e}")
    
    uvicorn.run(app, host="0.0.0.0", port=port)

