# 🏗️ REGLAS DE ARQUITECTURA RAG - SISTEMA DE INGESTA

## 📋 CONTEXTO DEL PROYECTO

Este proyecto implementa un sistema RAG (Retrieval-Augmented Generation) para procesar y consultar documentos (principalmente libros en PDF) usando:

- **Framework**: LlamaIndex (Python)
- **Embeddings**: OpenAI `text-embedding-3-small` (1536 dimensiones)
- **Vector Store**: Supabase con pgvector (PostgreSQL)
- **Modelo de embeddings**: `text-embedding-3-small`
- **Tier OpenAI**: Tier 3 con límites:
  - 5,000 RPM (requests por minuto)
  - 5,000,000 TPM (tokens por minuto)
  - 100,000,000 TPD (tokens por día)

## 🎯 OBJETIVO DE RENDIMIENTO

**Usar aproximadamente el 70% de la capacidad de Tier 3** para mantener estabilidad:
- **RPM objetivo**: 3,500 (70% de 5,000)
- **TPM objetivo**: 3,500,000 (70% de 5,000,000)
- **NO exceder estos límites** salvo solicitud explícita del usuario

## ⚙️ CONFIGURACIÓN POR DEFECTO (OBLIGATORIA)

### Chunking
- **Chunk size**: **1024 caracteres** (NO tokens, caracteres)
- **Chunk overlap**: **200 caracteres**
- **Splitter**: `SentenceSplitter` de LlamaIndex
- **Excepción**: Solo cambiar si el usuario lo solicita explícitamente

### Embeddings
- **Modelo**: `text-embedding-3-small` (1536 dimensiones)
- **Batch size para embeddings**: **30-40 chunks por request** (por defecto: 30)
- **Excepción**: Solo cambiar si el usuario lo solicita explícitamente

### Workers y Concurrencia
- **Número de workers por defecto**: **15**
- **Debe ser configurable** mediante variable de entorno `MAX_WORKERS`
- **Soporte para procesamiento paralelo** usando `asyncio` o `concurrent.futures`

### Base de Datos
- **Vector Store**: Supabase con pgvector
- **Dimensiones**: 1536 (compatible con `text-embedding-3-small`)
- **Metadatos obligatorios a guardar**:
  - `file_name`: Nombre del archivo
  - `chunk_id`: ID/número del chunk
  - `chunk_index`: Índice del chunk en el documento
  - `char_range`: Rango de caracteres (start, end)
  - `page_range`: Rango de páginas (si está disponible)
  - `book_title`: Título del libro/documento
  - `total_chunks`: Total de chunks del documento

## 🔒 REGLAS DE CÓDIGO

### 1. Chunking
```python
# SIEMPRE usar esta configuración por defecto:
from llama_index.core.node_parser import SentenceSplitter

text_splitter = SentenceSplitter(
    chunk_size=1024,      # 1024 caracteres (NO tokens)
    chunk_overlap=200    # 200 caracteres de overlap
)
```

**NO cambiar estos valores** salvo solicitud explícita del usuario.

### 2. Embeddings
```python
# SIEMPRE usar este modelo por defecto:
from llama_index.embeddings.openai import OpenAIEmbedding

embed_model = OpenAIEmbedding(model="text-embedding-3-small")
```

**NO cambiar el modelo** salvo solicitud explícita del usuario.

### 3. Batch Size para Embeddings
- **Por defecto**: 30 chunks por request a OpenAI
- **Rango permitido**: 30-40 chunks
- **Configurable mediante**: Variable de entorno `EMBEDDING_BATCH_SIZE`

### 4. Rate Limiting y Control de Carga
- **Implementar sistema de throttling** que respete:
  - Máximo 3,500 RPM (70% de 5,000)
  - Máximo 3,500,000 TPM (70% de 5,000,000)
- **Usar semáforos o rate limiters** para controlar la tasa de requests
- **Monitorear en tiempo real** el uso de RPM/TPM

### 5. Manejo de Errores
- **Errores 429 (Rate Limit)**:
  - Implementar backoff exponencial
  - Reintentos automáticos (máximo 5 intentos)
  - Logging detallado del error y tiempo de espera
- **Errores de red**:
  - Reintentos con backoff exponencial
  - Timeout configurable (por defecto: 30 segundos)
- **Errores de procesamiento**:
  - Registrar archivo y chunk que falló
  - Continuar con el siguiente archivo (no detener todo el proceso)
  - Guardar lista de archivos fallidos para reintento posterior

### 6. Logging y Monitoreo
**Logging obligatorio**:
- Archivos procesados (total y exitosos)
- Chunks generados (total)
- Tiempo por archivo (promedio y total)
- Errores (tipo, archivo, chunk)
- Uso de RPM/TPM en tiempo real
- Archivos sospechosos (menos de 5 chunks)

**Formato de logs**:
```python
# Usar logging estándar de Python con niveles apropiados
import logging

logging.info(f"Archivo procesado: {file_name} ({chunks} chunks)")
logging.warning(f"Archivo sospechoso: {file_name} (solo {chunks} chunks)")
logging.error(f"Error procesando {file_name}: {error}")
```

### 7. Archivos Sospechosos
- **Marcar como sospechosos** archivos con menos de 5 chunks
- **Registrar en log** con nivel WARNING
- **Incluir en reporte final** para revisión manual

### 8. Configuración
- **Usar variables de entorno** para parámetros críticos:
  - `MAX_WORKERS`: Número de workers (default: 15)
  - `EMBEDDING_BATCH_SIZE`: Chunks por request (default: 30)
  - `CHUNK_SIZE`: Tamaño de chunk (default: 1024) - **NO cambiar sin solicitud**
  - `CHUNK_OVERLAP`: Overlap de chunks (default: 200) - **NO cambiar sin solicitud**
  - `OPENAI_RPM_TARGET`: RPM objetivo (default: 3500)
  - `OPENAI_TPM_TARGET`: TPM objetivo (default: 3500000)
- **Archivo de configuración alternativo**: `config_ingesta.py` o similar

### 9. Estructura del Pipeline
El pipeline DEBE seguir este flujo estricto:

```
1. Leer PDF/archivo
   ↓
2. Extraer texto (SimpleDirectoryReader)
   ↓
3. Dividir en chunks (SentenceSplitter con 1024/200)
   ↓
4. Enviar embeddings a OpenAI en lotes (batch size 30-40)
   ↓
5. Guardar embeddings + metadatos en Supabase
```

**NO saltar pasos** ni combinar operaciones de forma que comprometa la claridad.

### 10. Reporte Final
Al terminar la ingesta, generar reporte con:
- Número de archivos procesados (exitosos y fallidos)
- Número total de chunks generados
- Tiempo total de procesamiento
- Tiempo promedio por archivo
- Lista de archivos con menos de 5 chunks (sospechosos)
- Lista de archivos fallidos (para reintento)
- Estadísticas de uso de RPM/TPM

## 🚫 PROHIBICIONES

1. **NO cambiar chunk size u overlap** sin solicitud explícita del usuario
2. **NO cambiar el modelo de embeddings** sin solicitud explícita del usuario
3. **NO exceder el 70% de los límites de Tier 3** (3,500 RPM, 3,500,000 TPM)
4. **NO procesar sin logging** adecuado
5. **NO ignorar errores** - siempre registrar y manejar
6. **NO usar batch sizes mayores a 40** para embeddings

## ✅ MEJORES PRÁCTICAS

1. **Código modular**: Separar lectura, chunking, embeddings y almacenamiento
2. **Configuración centralizada**: Usar variables de entorno o archivo de config
3. **Manejo robusto de errores**: Try-catch en cada etapa crítica
4. **Logging detallado**: Facilitar debugging y monitoreo
5. **Documentación**: Comentar código complejo o crítico
6. **Testing**: Probar con archivos pequeños antes de procesar lotes grandes

## 📝 NOTAS IMPORTANTES

- Estas reglas aplican a **TODO el repositorio** (`**/*`)
- Cualquier cambio a los valores por defecto debe ser **explícitamente solicitado** por el usuario
- El objetivo es mantener un sistema **rápido, estable y dentro de los límites de OpenAI Tier 3**

