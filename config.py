"""
Archivo de configuración para personalizar el chatbot según el dominio/tema.

Este archivo permite reutilizar el código base para diferentes proyectos:
- Cocina
- Psicología
- Trading
- Medicina
- Cualquier otro dominio

Simplemente modifica los valores según tu proyecto.
"""

# ============================================================================
# CONFIGURACIÓN DEL DOMINIO/TEMA
# ============================================================================

# Nombre del dominio/tema de tu proyecto
DOMAIN_NAME = "trading"

# Descripción del asistente (se usa en el prompt del sistema)
ASSISTANT_DESCRIPTION = "Eres un asistente experto en trading y psicología del trading. Responde basándote en el contexto proporcionado."

# Título de la API (aparece en la documentación de FastAPI)
API_TITLE = "Chat Bot API - Trading"

# Descripción de la API
API_DESCRIPTION = "API para consultar documentos indexados sobre trading con sistema de tokens"

# Nombre de la colección de vectores en Supabase
# Puedes usar el mismo nombre para todos los proyectos o cambiarlo por dominio
VECTOR_COLLECTION_NAME = "knowledge"

# Carpeta donde están los documentos a indexar
DATA_DIRECTORY = "./data"

# ============================================================================
# CONFIGURACIÓN AVANZADA (opcional)
# ============================================================================

# Número de documentos similares a recuperar para el contexto
SIMILARITY_TOP_K = 5

# Temperatura del modelo (creatividad: 0.0 = conservador, 1.0 = creativo)
MODEL_TEMPERATURE = 0.7

# Tokens iniciales para nuevos usuarios
INITIAL_TOKENS = 20000

# ============================================================================
# EJEMPLOS DE CONFIGURACIÓN PARA OTROS DOMINIOS
# ============================================================================

# Para un proyecto de COCINA:
# DOMAIN_NAME = "cocina"
# ASSISTANT_DESCRIPTION = "Eres un asistente experto en cocina, recetas y técnicas culinarias. Responde basándote en el contexto proporcionado."
# API_TITLE = "Chat Bot API - Cocina"
# API_DESCRIPTION = "API para consultar recetas y técnicas culinarias indexadas con sistema de tokens"

# Para un proyecto de PSICOLOGÍA:
# DOMAIN_NAME = "psicologia"
# ASSISTANT_DESCRIPTION = "Eres un asistente experto en psicología y salud mental. Responde basándote en el contexto proporcionado."
# API_TITLE = "Chat Bot API - Psicología"
# API_DESCRIPTION = "API para consultar documentos sobre psicología indexados con sistema de tokens"

# Para un proyecto de MEDICINA:
# DOMAIN_NAME = "medicina"
# ASSISTANT_DESCRIPTION = "Eres un asistente experto en medicina y salud. Responde basándote en el contexto proporcionado."
# API_TITLE = "Chat Bot API - Medicina"
# API_DESCRIPTION = "API para consultar documentos médicos indexados con sistema de tokens"

