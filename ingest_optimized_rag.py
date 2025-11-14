"""
🚀 PIPELINE DE INGESTA RAG OPTIMIZADO
======================================

Pipeline optimizado siguiendo las reglas de arquitectura RAG:
- Chunk size: 1024 caracteres, overlap: 200
- Batch size: 30-40 chunks por request
- 15 workers por defecto
- Control de rate limits al 70% de Tier 3
- Logging robusto y reporte final

Autor: Arquitecto RAG
Fecha: 2025-11-13
"""

import os
import sys
import time
import json
import logging
import traceback
from datetime import datetime, timedelta
from urllib.parse import quote_plus
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
import threading

from dotenv import load_dotenv
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext, Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import TextNode
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.supabase import SupabaseVectorStore
import psycopg2
from psycopg2.extras import RealDictCursor

import config
import config_ingesta
from ingestion_monitor import IngestionMonitor, generate_report, RICH_AVAILABLE
from anti_duplicates import (
    ensure_documents_table,
    calculate_doc_id,
    calculate_chunk_id,
    decide_document_action,
    register_document,
    update_document_chunks,
    delete_document_chunks,
    check_chunk_exists,
    DocumentDecision,
    FORCE_REINDEX
)
from metadata_extractor import extract_rich_metadata
from error_logger import (
    ensure_errors_table,
    log_error,
    ErrorType,
    get_error_summary,
    get_recent_errors
)

# Configurar encoding para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# ============================================================================
# CONFIGURACIÓN DE LOGGING
# ============================================================================

logging.basicConfig(
    level=getattr(logging, config_ingesta.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config_ingesta.LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# ============================================================================
# CLASES DE DATOS
# ============================================================================

@dataclass
class ProcessingStats:
    """Estadísticas de procesamiento"""
    files_processed: int = 0
    files_failed: int = 0
    chunks_generated: int = 0
    total_time: float = 0.0
    suspicious_files: List[str] = None
    failed_files: List[Dict] = None
    rpm_usage: float = 0.0
    tpm_usage: float = 0.0
    
    def __post_init__(self):
        if self.suspicious_files is None:
            self.suspicious_files = []
        if self.failed_files is None:
            self.failed_files = []

@dataclass
class FileMetadata:
    """Metadatos de un archivo procesado"""
    file_name: str
    file_path: str
    total_chunks: int
    char_ranges: List[Tuple[int, int]]
    page_ranges: Optional[List[Tuple[int, int]]] = None
    book_title: Optional[str] = None

# ============================================================================
# CONFIGURACIÓN Y VARIABLES GLOBALES
# ============================================================================

load_dotenv()

def get_env(key, default=None):
    """Obtiene variable de entorno"""
    value = os.getenv(key, default)
    if not value:
        for env_key in os.environ.keys():
            if env_key.strip().lstrip('\ufeff') == key:
                value = os.environ[env_key]
                break
    return value.strip('"').strip("'").strip() if value else default

# Variables de entorno
SUPABASE_URL = get_env("SUPABASE_URL")
SUPABASE_SERVICE_KEY = get_env("SUPABASE_SERVICE_KEY")
OPENAI_API_KEY = get_env("OPENAI_API_KEY")
SUPABASE_DB_PASSWORD = get_env("SUPABASE_DB_PASSWORD")

if not all([SUPABASE_URL, SUPABASE_SERVICE_KEY, OPENAI_API_KEY, SUPABASE_DB_PASSWORD]):
    raise ValueError("Faltan variables de entorno necesarias")

# Configurar Supabase
project_ref = SUPABASE_URL.replace("https://", "").replace(".supabase.co", "")
encoded_password = quote_plus(SUPABASE_DB_PASSWORD)
postgres_connection_string = f"postgresql://postgres:{encoded_password}@db.{project_ref}.supabase.co:5432/postgres"

# Nombre de colección
collection_name = config_ingesta.VECTOR_COLLECTION_NAME or config.VECTOR_COLLECTION_NAME

# ============================================================================
# CONFIGURACIÓN DE COMPONENTES
# ============================================================================

# Text splitter con configuración fija (1024 caracteres, 200 overlap)
text_splitter = SentenceSplitter(
    chunk_size=config_ingesta.CHUNK_SIZE,
    chunk_overlap=config_ingesta.CHUNK_OVERLAP
)

# Embed model (text-embedding-3-small)
embed_model = OpenAIEmbedding(model=config_ingesta.EMBEDDING_MODEL)

# Vector store
vector_store = SupabaseVectorStore(
    postgres_connection_string=postgres_connection_string,
    collection_name=collection_name
)

storage_context = StorageContext.from_defaults(vector_store=vector_store)

# ============================================================================
# CONTROL DE RATE LIMITING
# ============================================================================

class RateLimiter:
    """Controlador de rate limits para respetar límites de OpenAI"""
    
    def __init__(self, rpm_target: int, tpm_target: int):
        self.rpm_target = rpm_target
        self.tpm_target = tpm_target
        self.request_times = []
        self.token_usage = []
        self.lock = threading.Lock()
        self.min_interval = 60.0 / rpm_target  # Intervalo mínimo entre requests
        
    def wait_if_needed(self):
        """Espera si es necesario para respetar rate limits"""
        with self.lock:
            now = time.time()
            # Limpiar requests antiguos (último minuto)
            self.request_times = [t for t in self.request_times if now - t < 60]
            
            if len(self.request_times) >= self.rpm_target:
                # Esperar hasta que haya espacio
                oldest = min(self.request_times)
                wait_time = 60 - (now - oldest) + 0.1  # Pequeño margen
                if wait_time > 0:
                    logger.debug(f"Rate limit: esperando {wait_time:.2f}s")
                    time.sleep(wait_time)
            
            self.request_times.append(time.time())
    
    def record_tokens(self, tokens: int):
        """Registra uso de tokens"""
        with self.lock:
            now = time.time()
            self.token_usage.append((now, tokens))
            # Limpiar tokens antiguos
            self.token_usage = [(t, tok) for t, tok in self.token_usage if now - t < 60]
            
            total_tokens = sum(tok for _, tok in self.token_usage)
            if total_tokens >= self.tpm_target:
                logger.warning(f"TPM cerca del límite: {total_tokens:,}/{self.tpm_target:,}")
    
    def get_current_usage(self) -> Tuple[float, float]:
        """Retorna uso actual (RPM, TPM)"""
        with self.lock:
            now = time.time()
            recent_requests = len([t for t in self.request_times if now - t < 60])
            recent_tokens = sum(tok for t, tok in self.token_usage if now - t < 60)
            return recent_requests, recent_tokens

# Instancia global del rate limiter
rate_limiter = RateLimiter(
    config_ingesta.OPENAI_RPM_TARGET,
    config_ingesta.OPENAI_TPM_TARGET
)

# ============================================================================
# MANEJO DE ERRORES CON BACKOFF EXPONENCIAL
# ============================================================================

def retry_with_backoff(func, max_retries=config_ingesta.MAX_RETRIES, worker_id=None):
    """Ejecuta función con reintentos y backoff exponencial"""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            error_str = str(e).lower()
            error_code = getattr(e, 'status_code', None)
            
            # Detectar rate limit (429)
            if 'rate limit' in error_str or '429' in error_str or error_code == 429:
                wait_time = (2 ** attempt) + (attempt * 0.5)
                worker_msg = f"[Worker {worker_id}] " if worker_id else ""
                logger.warning(f"{worker_msg}Rate limit (429), esperando {wait_time:.1f}s...")
                time.sleep(wait_time)
            else:
                if attempt < max_retries - 1:
                    wait_time = 1.0 * (attempt + 1)
                    time.sleep(wait_time)
                else:
                    raise
    raise Exception(f"Error después de {max_retries} intentos")

# ============================================================================
# PROCESAMIENTO DE ARCHIVOS
# ============================================================================

def extract_text_from_file(file_path: str) -> List[Document]:
    """
    Paso 1 y 2: Leer PDF y extraer texto
    
    Returns:
        Lista de documentos con texto extraído
    """
    try:
        reader = SimpleDirectoryReader(input_files=[file_path])
        documents = reader.load_data()
        return documents
    except Exception as e:
        logger.error(f"Error extrayendo texto de {file_path}: {e}")
        raise

def split_into_chunks(documents: List[Document]) -> List[Document]:
    """
    Paso 3: Dividir en chunks usando SentenceSplitter
    
    Returns:
        Lista de documentos (chunks) con metadatos
    """
    all_chunks = []
    for doc in documents:
        # Usar el text splitter configurado para dividir el documento
        nodes = text_splitter.get_nodes_from_documents([doc])
        # Convertir nodes a documentos manteniendo metadatos
        for node in nodes:
            chunk_doc = Document(
                text=node.text,
                metadata={
                    **node.metadata,
                    **doc.metadata  # Preservar metadatos originales
                }
            )
            all_chunks.append(chunk_doc)
    return all_chunks

def process_chunks_in_batches(chunks: List[Document], file_metadata: FileMetadata, doc_id: str, monitor: Optional[IngestionMonitor] = None) -> int:
    """
    Paso 4 y 5: Enviar embeddings en lotes y guardar en Supabase
    
    Args:
        chunks: Lista de chunks a procesar
        file_metadata: Metadatos del archivo
        
    Returns:
        Número de chunks procesados exitosamente
    """
    total_processed = 0
    
    # Procesar en lotes de EMBEDDING_BATCH_SIZE
    for i in range(0, len(chunks), config_ingesta.EMBEDDING_BATCH_SIZE):
        batch = chunks[i:i + config_ingesta.EMBEDDING_BATCH_SIZE]
        
        # Control de rate limit
        rate_limiter.wait_if_needed()
        
        # Filtrar chunks duplicados antes de procesar
        batch_to_process = []
        for idx, chunk in enumerate(batch):
            chunk_id = chunk.metadata.get('chunk_id')
            
            # Verificar si el chunk ya existe (anti-duplicados a nivel de chunk)
            if chunk_id and check_chunk_exists(chunk_id, collection_name):
                logger.debug(f"Chunk {chunk_id[:8]}... ya existe, saltando")
                continue  # Saltar chunk duplicado
            
            # Agregar metadatos al chunk
            chunk.metadata.update({
                'file_name': file_metadata.file_name,
                'chunk_index': i + idx,
                'total_chunks': file_metadata.total_chunks,
                'book_title': file_metadata.book_title or file_metadata.file_name,
            })
            
            # Agregar rango de caracteres si está disponible
            if i + idx < len(file_metadata.char_ranges):
                start, end = file_metadata.char_ranges[i + idx]
                chunk.metadata['char_range'] = f"{start}-{end}"
            
            batch_to_process.append(chunk)
        
        # Si no hay chunks nuevos en este batch, continuar
        if not batch_to_process:
            continue
        
        # Procesar batch con reintentos
        def process_batch():
            # Convertir documentos a nodes para insertar directamente
            nodes = []
            for chunk in batch_to_process:
                node = TextNode(
                    text=chunk.text,
                    metadata=chunk.metadata
                )
                nodes.append(node)
            
            # Crear índice temporal y agregar nodes
            # Esto generará embeddings automáticamente
            temp_index = VectorStoreIndex(
                nodes=nodes,
                storage_context=storage_context,
                embed_model=embed_model,
                show_progress=False
            )
            
            return len(batch)
        
        try:
            processed = retry_with_backoff(process_batch)
            total_processed += processed
            
            # Registrar tokens estimados (aproximación: 1 token ≈ 4 caracteres)
            estimated_tokens = sum(len(chunk.text) // 4 for chunk in batch_to_process)
            rate_limiter.record_tokens(estimated_tokens)
            
            # Notificar al monitor sobre el batch procesado
            if monitor:
                monitor.on_chunk_batch_processed(len(batch_to_process), estimated_tokens)
            
        except Exception as e:
            logger.error(f"Error procesando batch {i//config_ingesta.EMBEDDING_BATCH_SIZE + 1}: {e}")
            # Notificar reintento si es rate limit
            if "429" in str(e) or "rate limit" in str(e).lower():
                if monitor:
                    monitor.on_rate_limit_retry()
            # Continuar con siguiente batch
    
    return total_processed

def process_single_file(file_path: str, worker_id: Optional[int] = None, monitor: Optional[IngestionMonitor] = None) -> Tuple[bool, FileMetadata, int, str]:
    """
    Procesa un archivo completo siguiendo el pipeline:
    1. Calcular doc_id (hash del archivo)
    2. Verificar si ya existe (anti-duplicados)
    3. Leer PDF
    4. Extraer texto
    5. Dividir en chunks
    6. Enviar embeddings en lotes
    7. Guardar en Supabase
    
    Args:
        file_path: Ruta del archivo a procesar
        worker_id: ID del worker (opcional)
        monitor: Instancia del monitor (opcional)
    
    Returns:
        (success, metadata, chunks_count, decision) donde decision es 'skip', 'process', o 'reindex'
    """
    file_name = os.path.basename(file_path)
    worker_msg = f"[Worker {worker_id}] " if worker_id else ""
    
    # ========================================================================
    # ANTI-DUPLICADOS: Calcular doc_id y verificar
    # ========================================================================
    try:
        doc_id = calculate_doc_id(file_path)
    except Exception as e:
        logger.error(f"{worker_msg}❌ {file_name}: Error calculando hash: {e}")
        if monitor:
            monitor.on_file_error(file_name, f"Error calculando hash: {e}", "hash")
        return False, None, 0, "error"
    
    # Decidir acción: skip, process, o reindex
    action, existing_doc = decide_document_action(doc_id, force_reindex=FORCE_REINDEX)
    
    if action == DocumentDecision.SKIP:
        logger.info(f"{worker_msg}⏭️  {file_name}: Duplicado detectado (doc_id: {doc_id[:8]}...), saltando")
        if monitor:
            monitor.on_file_duplicate(file_name, doc_id)
        return False, None, 0, "skip"
    
    if action == DocumentDecision.REINDEX:
        logger.info(f"{worker_msg}🔄 {file_name}: Reindexando (doc_id: {doc_id[:8]}...)")
        # Eliminar chunks existentes
        deleted = delete_document_chunks(doc_id, collection_name)
        logger.info(f"{worker_msg}   Eliminados {deleted} chunks anteriores")
        if monitor:
            monitor.on_file_reindex(file_name, doc_id, deleted)
    
    # Notificar al monitor que se inició el archivo
    if monitor:
        monitor.on_file_started(file_name, file_path)
    
    try:
        start_time = time.time()
        
        # Paso 1 y 2: Leer y extraer texto
        logger.info(f"{worker_msg}Procesando: {file_name} (doc_id: {doc_id[:8]}...)")
        
        try:
            documents = extract_text_from_file(file_path)
        except Exception as e:
            error_msg = f"Error extrayendo texto: {str(e)}"
            logger.error(f"{worker_msg}❌ {file_name}: {error_msg}")
            
            # Registrar error en Supabase
            log_error(
                filename=file_name,
                error_type=ErrorType.EXTRACTION_ERROR,
                error_message=error_msg,
                doc_id=doc_id,
                exception=e
            )
            
            if monitor:
                monitor.on_file_error(file_name, error_msg, "extraction")
            return False, None, 0, "error"
        
        if not documents:
            logger.warning(f"{worker_msg}{file_name}: Sin contenido")
            
            # Registrar error en Supabase
            log_error(
                filename=file_name,
                error_type=ErrorType.EXTRACTION_ERROR,
                error_message="Sin contenido extraído del archivo",
                doc_id=doc_id
            )
            
            if monitor:
                monitor.on_file_error(file_name, "Sin contenido extraído", "extraction")
            return False, None, 0, "error"
        
        # Extraer texto completo para metadatos
        full_text = " ".join([doc.text for doc in documents])
        
        # ========================================================================
        # EXTRACCIÓN DE METADATOS RICOS
        # ========================================================================
        try:
            rich_metadata = extract_rich_metadata(file_path, text=full_text)
            logger.info(f"{worker_msg}📚 Metadatos: {rich_metadata.get('title', 'N/A')} | "
                       f"Autor: {rich_metadata.get('author', 'N/A')} | "
                       f"Idioma: {rich_metadata.get('language', 'unknown')} | "
                       f"Categoría: {rich_metadata.get('category', 'general')}")
        except Exception as e:
            logger.warning(f"{worker_msg}⚠️  Error extrayendo metadatos: {e}")
            # Continuar sin metadatos ricos
            rich_metadata = {
                'title': file_name,
                'author': None,
                'language': 'unknown',
                'category': 'general',
                'published_year': None
            }
            
            # Registrar error (no crítico)
            log_error(
                filename=file_name,
                error_type=ErrorType.METADATA_ERROR,
                error_message=f"Error extrayendo metadatos: {str(e)}",
                doc_id=doc_id,
                exception=e
            )
        
        # Paso 3: Dividir en chunks
        try:
            chunks = split_into_chunks(documents)
        except Exception as e:
            error_msg = f"Error dividiendo en chunks: {str(e)}"
            logger.error(f"{worker_msg}❌ {file_name}: {error_msg}")
            
            # Registrar error en Supabase
            log_error(
                filename=file_name,
                error_type=ErrorType.CHUNKING_ERROR,
                error_message=error_msg,
                doc_id=doc_id,
                exception=e
            )
            
            if monitor:
                monitor.on_file_error(file_name, error_msg, "chunking")
            return False, None, 0, "error"
        
        if not chunks:
            logger.warning(f"{worker_msg}{file_name}: No se generaron chunks")
            
            # Registrar error en Supabase
            log_error(
                filename=file_name,
                error_type=ErrorType.CHUNKING_ERROR,
                error_message="No se generaron chunks del documento",
                doc_id=doc_id
            )
            
            if monitor:
                monitor.on_file_error(file_name, "No se generaron chunks", "chunking")
            return False, None, 0, "error"
        
        # Crear metadatos
        char_ranges = []
        current_char = 0
        for chunk in chunks:
            start = current_char
            end = current_char + len(chunk.text)
            char_ranges.append((start, end))
            current_char = end
        
        file_metadata = FileMetadata(
            file_name=file_name,
            file_path=file_path,
            total_chunks=len(chunks),
            char_ranges=char_ranges,
            book_title=rich_metadata.get('title', file_name)  # Usar título extraído
        )
        
        # Agregar doc_id a metadatos de cada chunk
        for idx, chunk in enumerate(chunks):
            chunk.metadata['doc_id'] = doc_id
            # Calcular chunk_id determinístico
            chunk_id = calculate_chunk_id(doc_id, idx, chunk.text)
            chunk.metadata['chunk_id'] = chunk_id
        
        # Paso 4 y 5: Procesar chunks en lotes y guardar
        processed_chunks = process_chunks_in_batches(chunks, file_metadata, doc_id=doc_id, monitor=monitor)
        
        elapsed = time.time() - start_time
        logger.info(f"{worker_msg}✅ {file_name}: {processed_chunks} chunks en {elapsed:.2f}s")
        
        # Verificar si es sospechoso (menos de 5 chunks)
        is_suspicious = processed_chunks < config_ingesta.MIN_CHUNKS_PER_FILE
        if is_suspicious:
            logger.warning(f"{worker_msg}⚠️  {file_name}: Solo {processed_chunks} chunks (archivo sospechoso)")
        
        # Registrar documento en tabla documents con metadatos ricos
        register_document(
            doc_id=doc_id,
            filename=file_name,
            file_path=file_path,
            title=rich_metadata.get('title', file_metadata.book_title),
            author=rich_metadata.get('author'),
            language=rich_metadata.get('language', 'unknown'),
            category=rich_metadata.get('category', 'general'),
            published_year=rich_metadata.get('published_year'),
            total_chunks=processed_chunks
        )
        
        # Notificar al monitor que se completó el archivo
        if monitor:
            monitor.on_file_completed(file_name, processed_chunks, is_suspicious=is_suspicious)
        
        return True, file_metadata, processed_chunks, action
        
    except Exception as e:
        logger.error(f"{worker_msg}❌ {file_name}: {e}")
        logger.debug(traceback.format_exc())
        
        # Determinar tipo de error
        if "429" in str(e) or "rate limit" in str(e).lower():
            error_type = ErrorType.RATE_LIMIT_ERROR
        elif "openai" in str(e).lower() or "api" in str(e).lower():
            error_type = ErrorType.OPENAI_ERROR
        elif "network" in str(e).lower() or "connection" in str(e).lower():
            error_type = ErrorType.NETWORK_ERROR
        else:
            error_type = ErrorType.UNKNOWN_ERROR
        
        # Registrar error en Supabase
        try:
            log_error(
                filename=file_name,
                error_type=error_type,
                error_message=str(e),
                doc_id=doc_id if 'doc_id' in locals() else None,
                exception=e
            )
        except:
            pass  # Si falla el logging, continuar
        
        # Notificar error al monitor
        if monitor:
            monitor_error_type = "rate_limit" if error_type == ErrorType.RATE_LIMIT_ERROR else "other"
            monitor.on_file_error(file_name, str(e), monitor_error_type)
        
        return False, None, 0, "error"

# ============================================================================
# WORKERS Y CONCURRENCIA
# ============================================================================

def worker_function(worker_id: int, file_queue: Queue, results_queue: Queue, stats: ProcessingStats, monitor: Optional[IngestionMonitor] = None):
    """Función que ejecuta cada worker"""
    logger.info(f"[Worker {worker_id}] Iniciado")
    
    while True:
        try:
            file_path = file_queue.get(timeout=5)
            
            if file_path is None:  # Señal de terminación
                break
            
            success, metadata, chunks, decision = process_single_file(file_path, worker_id, monitor=monitor)
            
            with threading.Lock():
                if decision == "skip":
                    # Archivo duplicado, ya fue registrado en el monitor
                    pass
                elif success:
                    stats.files_processed += 1
                    stats.chunks_generated += chunks
                    
                    if metadata and metadata.total_chunks < config_ingesta.MIN_CHUNKS_PER_FILE:
                        stats.suspicious_files.append(metadata.file_name)
                else:
                    stats.files_failed += 1
                    stats.failed_files.append({
                        'file_path': file_path,
                        'error': 'Procesamiento fallido',
                        'timestamp': datetime.now().isoformat()
                    })
            
            results_queue.put({
                'worker_id': worker_id,
                'success': success,
                'file_name': os.path.basename(file_path),
                'chunks': chunks
            })
            
            file_queue.task_done()
            
        except Exception as e:
            if "timeout" not in str(e).lower():
                logger.error(f"[Worker {worker_id}] Error: {e}")
            break
    
    logger.info(f"[Worker {worker_id}] Finalizado")

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def get_indexed_files() -> set:
    """Obtiene lista de archivos ya indexados"""
    try:
        conn = psycopg2.connect(postgres_connection_string, connect_timeout=10)
        cur = conn.cursor()
        cur.execute("SET statement_timeout = '15s'")
        
        cur.execute(f"""
            SELECT DISTINCT metadata->>'file_name' as file_name
            FROM vecs.{collection_name}
            WHERE metadata->>'file_name' IS NOT NULL
        """)
        
        indexed = {row[0] for row in cur.fetchall()}
        cur.close()
        conn.close()
        return indexed
    except Exception as e:
        logger.warning(f"Error obteniendo archivos indexados: {e}")
        return set()

def get_files_to_process() -> Tuple[List[str], int]:
    """
    Obtiene lista de archivos pendientes de procesar
    
    NOTA: Ya no filtra por nombre de archivo aquí.
    El sistema anti-duplicados verificará por hash (doc_id) antes de procesar cada archivo.
    Esto permite detectar duplicados incluso si el archivo tiene diferente nombre.
    """
    data_dir = Path(config.DATA_DIRECTORY)
    supported_extensions = {'.pdf', '.epub', '.txt', '.docx', '.md', '.doc'}
    
    all_files = []
    if data_dir.exists():
        for file_path in data_dir.rglob('*'):
            if file_path.suffix.lower() in supported_extensions:
                all_files.append(str(file_path))
    
    # NO filtrar aquí - el anti-duplicados lo hará por hash
    # Esto permite detectar duplicados incluso con nombres diferentes
    
    return all_files, len(all_files)

# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def generate_final_report_legacy(stats: ProcessingStats, start_time: float):
    """Genera reporte final de la ingesta (método legacy, mantenido por compatibilidad)"""
    total_time = time.time() - start_time
    stats.total_time = total_time
    
    # Obtener uso actual de rate limits
    rpm_usage, tpm_usage = rate_limiter.get_current_usage()
    stats.rpm_usage = rpm_usage
    stats.tpm_usage = tpm_usage
    
    report = f"""
{'='*80}
📊 REPORTE FINAL DE INGESTA
{'='*80}

📚 ARCHIVOS:
   • Procesados exitosamente: {stats.files_processed}
   • Fallidos: {stats.files_failed}
   • Total: {stats.files_processed + stats.files_failed}

📦 CHUNKS:
   • Total generados: {stats.chunks_generated}
   • Promedio por archivo: {stats.chunks_generated / stats.files_processed if stats.files_processed > 0 else 0:.1f}

⏱️  TIEMPO:
   • Tiempo total: {int(total_time // 3600)}h {int((total_time % 3600) // 60)}m {int(total_time % 60)}s
   • Tiempo promedio por archivo: {total_time / stats.files_processed if stats.files_processed > 0 else 0:.2f}s

⚠️  ARCHIVOS SOSPECHOSOS (< {config_ingesta.MIN_CHUNKS_PER_FILE} chunks):
"""
    
    if stats.suspicious_files:
        for file_name in stats.suspicious_files:
            report += f"   • {file_name}\n"
    else:
        report += "   • Ninguno\n"
    
    report += f"""
❌ ARCHIVOS FALLIDOS:
"""
    
    if stats.failed_files:
        for failed in stats.failed_files[:10]:  # Mostrar primeros 10
            report += f"   • {failed['file_path']}\n"
        if len(stats.failed_files) > 10:
            report += f"   ... y {len(stats.failed_files) - 10} más\n"
    else:
        report += "   • Ninguno\n"
    
    report += f"""
📈 USO DE RATE LIMITS:
   • RPM actual: {rpm_usage:.0f}/{config_ingesta.OPENAI_RPM_TARGET} ({rpm_usage/config_ingesta.OPENAI_RPM_TARGET*100:.1f}%)
   • TPM actual: {tpm_usage:,.0f}/{config_ingesta.OPENAI_TPM_TARGET:,} ({tpm_usage/config_ingesta.OPENAI_TPM_TARGET*100:.1f}%)

{'='*80}
"""
    
    logger.info(report)
    print(report)
    
    # Guardar reporte en archivo
    report_file = f"reporte_ingesta_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info(f"Reporte guardado en: {report_file}")

def main():
    """Función principal del pipeline de ingesta"""
    logger.info("="*80)
    logger.info("🚀 INICIANDO PIPELINE DE INGESTA RAG OPTIMIZADO")
    logger.info("="*80)
    logger.info(f"Configuración:")
    logger.info(f"  • Chunk size: {config_ingesta.CHUNK_SIZE} caracteres")
    logger.info(f"  • Chunk overlap: {config_ingesta.CHUNK_OVERLAP} caracteres")
    logger.info(f"  • Embedding batch size: {config_ingesta.EMBEDDING_BATCH_SIZE}")
    logger.info(f"  • Workers: {config_ingesta.MAX_WORKERS}")
    logger.info(f"  • RPM objetivo: {config_ingesta.OPENAI_RPM_TARGET}")
    logger.info(f"  • TPM objetivo: {config_ingesta.OPENAI_TPM_TARGET:,}")
    logger.info(f"  • Force reindex: {FORCE_REINDEX}")
    logger.info("="*80)
    
    # ========================================================================
    # ASEGURAR TABLAS (ANTI-DUPLICADOS + ERRORES)
    # ========================================================================
    logger.info("🔒 Inicializando sistema anti-duplicados...")
    if ensure_documents_table():
        logger.info("✅ Tabla 'documents' verificada/creada (con metadatos ricos)")
    else:
        logger.warning("⚠️  No se pudo crear/verificar tabla 'documents', continuando...")
    
    logger.info("🔴 Inicializando sistema de logging de errores...")
    if ensure_errors_table():
        logger.info("✅ Tabla 'ingestion_errors' verificada/creada")
    else:
        logger.warning("⚠️  No se pudo crear/verificar tabla 'ingestion_errors', continuando...")
    
    start_time = time.time()
    stats = ProcessingStats()
    
    # Obtener archivos a procesar (ahora sin filtrar por nombre, el anti-duplicados lo hará por hash)
    files_to_process, total_files = get_files_to_process()
    
    if not files_to_process:
        logger.info("✅ Todos los archivos ya están indexados.")
        return
    
    logger.info(f"📚 Archivos a procesar: {len(files_to_process)}/{total_files}")
    
    # ========================================================================
    # INICIALIZAR MONITOR PROFESIONAL
    # ========================================================================
    monitor = IngestionMonitor(total_files=len(files_to_process))
    monitor.start()
    logger.info("📊 Monitor en tiempo real iniciado")
    
    # Crear colas para workers
    file_queue = Queue()
    results_queue = Queue()
    
    # Agregar archivos a la cola
    for file_path in files_to_process:
        file_queue.put(file_path)
    
    # Iniciar workers
    logger.info(f"🚀 Iniciando {config_ingesta.MAX_WORKERS} workers...")
    
    try:
        with ThreadPoolExecutor(max_workers=config_ingesta.MAX_WORKERS) as executor:
            # Iniciar todos los workers
            futures = []
            for worker_id in range(1, config_ingesta.MAX_WORKERS + 1):
                future = executor.submit(worker_function, worker_id, file_queue, results_queue, stats, monitor=monitor)
                futures.append(future)
        
            # Agregar señales de terminación
            for _ in range(config_ingesta.MAX_WORKERS):
                file_queue.put(None)
            
            # Monitorear progreso (el monitor se encarga de mostrar actualizaciones)
            completed = 0
            
            while completed < len(files_to_process):
                try:
                    result = results_queue.get(timeout=1)
                    completed += 1
                except:
                    # Timeout, verificar si workers siguen activos
                    continue
            
            # Esperar a que todos los workers terminen
            for future in futures:
                future.result()
    finally:
        # Detener el monitor
        monitor.stop()
        logger.info("📊 Monitor detenido")
    
    # ========================================================================
    # GENERAR REPORTE FINAL PROFESIONAL
    # ========================================================================
    logger.info("\n" + "="*80)
    logger.info("📊 GENERANDO REPORTE FINAL...")
    logger.info("="*80)
    
    report_content, report_file = generate_report(monitor)
    
    # Mostrar reporte en consola
    if RICH_AVAILABLE:
        from rich.console import Console
        from rich.markdown import Markdown
        console = Console()
        console.print(Markdown(report_content))
    else:
        print(report_content)
    
    logger.info(f"\n✅ Reporte guardado en: {report_file}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n⏹️  Proceso interrumpido por el usuario")
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}")
        logger.debug(traceback.format_exc())

