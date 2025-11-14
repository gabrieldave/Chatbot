"""
⚙️ CONFIGURACIÓN CENTRALIZADA PARA INGESTA RAG
===============================================

Este archivo contiene todas las configuraciones del pipeline de ingesta.
Los valores pueden ser sobrescritos mediante variables de entorno.
"""

import os
from dotenv import load_dotenv

load_dotenv()

def get_env(key, default=None, type_cast=str):
    """Obtiene variable de entorno con tipo casting"""
    value = os.getenv(key, default)
    if value is None:
        return None
    try:
        return type_cast(value)
    except (ValueError, TypeError):
        return default

# ============================================================================
# CONFIGURACIÓN DE CHUNKING (NO CAMBIAR SIN SOLICITUD EXPLÍCITA)
# ============================================================================

# Chunk size: 1024 caracteres (NO tokens)
CHUNK_SIZE = get_env("CHUNK_SIZE", 1024, int)

# Chunk overlap: 200 caracteres
CHUNK_OVERLAP = get_env("CHUNK_OVERLAP", 200, int)

# ============================================================================
# CONFIGURACIÓN DE EMBEDDINGS
# ============================================================================

# Modelo de embeddings (NO CAMBIAR SIN SOLICITUD EXPLÍCITA)
EMBEDDING_MODEL = get_env("EMBEDDING_MODEL", "text-embedding-3-small")

# Batch size para embeddings: 30-40 chunks por request (REDUCIDO para evitar sobrecarga)
EMBEDDING_BATCH_SIZE = get_env("EMBEDDING_BATCH_SIZE", 20, int)  # Reducido de 30 a 20
if EMBEDDING_BATCH_SIZE < 15 or EMBEDDING_BATCH_SIZE > 40:
    raise ValueError(f"EMBEDDING_BATCH_SIZE debe estar entre 15 y 40, actual: {EMBEDDING_BATCH_SIZE}")

# ============================================================================
# CONFIGURACIÓN DE WORKERS Y CONCURRENCIA
# ============================================================================

# Número de workers paralelos (REDUCIDO para evitar sobrecarga en Supabase)
MAX_WORKERS = get_env("MAX_WORKERS", 5, int)  # Reducido de 15 a 5

# ============================================================================
# CONFIGURACIÓN DE LÍMITES OPENAI TIER 3
# ============================================================================

# Límites máximos de Tier 3
TIER3_RPM_LIMIT = 5000
TIER3_TPM_LIMIT = 5000000
TIER3_TPD_LIMIT = 100000000

# Objetivo: 57% de capacidad (REDUCIDO para dar margen a Supabase)
OPENAI_RPM_TARGET = get_env("OPENAI_RPM_TARGET", int(TIER3_RPM_LIMIT * 0.57), int)  # ~2,850 RPM
OPENAI_TPM_TARGET = get_env("OPENAI_TPM_TARGET", int(TIER3_TPM_LIMIT * 0.57), int)  # ~2,850,000 TPM

# Validar que no exceda el 70%
if OPENAI_RPM_TARGET > TIER3_RPM_LIMIT * 0.7:
    raise ValueError(f"OPENAI_RPM_TARGET no debe exceder 70% de {TIER3_RPM_LIMIT} (3,500)")
if OPENAI_TPM_TARGET > TIER3_TPM_LIMIT * 0.7:
    raise ValueError(f"OPENAI_TPM_TARGET no debe exceder 70% de {TIER3_TPM_LIMIT} (3,500,000)")

# ============================================================================
# CONFIGURACIÓN DE TIMEOUTS Y REINTENTOS
# ============================================================================

# Timeout para requests a OpenAI (segundos)
OPENAI_TIMEOUT = get_env("OPENAI_TIMEOUT", 30, int)

# Número máximo de reintentos para errores 429
MAX_RETRIES = get_env("MAX_RETRIES", 5, int)

# ============================================================================
# CONFIGURACIÓN DE LOGGING
# ============================================================================

# Nivel de logging
LOG_LEVEL = get_env("LOG_LEVEL", "INFO")

# Archivo de log
LOG_FILE = get_env("LOG_FILE", "ingesta.log")

# ============================================================================
# CONFIGURACIÓN DE ARCHIVOS SOSPECHOSOS
# ============================================================================

# Mínimo de chunks para considerar un archivo válido
MIN_CHUNKS_PER_FILE = get_env("MIN_CHUNKS_PER_FILE", 5, int)

# ============================================================================
# CONFIGURACIÓN DE SUPABASE
# ============================================================================

# Nombre de la colección (se obtiene de config.py normalmente)
# Se puede sobrescribir con variable de entorno
VECTOR_COLLECTION_NAME = get_env("VECTOR_COLLECTION_NAME", None)

