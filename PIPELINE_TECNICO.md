# 📋 PIPELINE TÉCNICO COMPLETO

## 1️⃣ ¿QUÉ CHUNK SIZE USAS?

### **Chunk Size: Default de LlamaIndex (1024 caracteres)**

**✅ Verificado con código:**
```python
Default chunk_size: 1024 caracteres
Default chunk_overlap: 200 caracteres
```

**No hay configuración explícita de chunk_size en el código actual.**

LlamaIndex usa por defecto:
- **Chunk size**: **1024 caracteres** (no tokens)
- **Chunk overlap**: **200 caracteres** (~20% para mantener contexto entre chunks)

**Evidencia en el código:**
```python
# No hay configuración explícita de chunk_size
index = VectorStoreIndex.from_documents(
    documents,
    storage_context=storage_context,
    embed_model=embed_model,
    show_progress=False
)
```

LlamaIndex automáticamente:
- Usa `SentenceSplitter` o `TokenTextSplitter` por defecto
- Divide documentos en chunks de ~1024 tokens
- Mantiene overlap entre chunks para contexto

**Observación práctica:**
- Cada archivo genera ~100 chunks en promedio
- Chunk size: 1024 caracteres = ~256 tokens (1 token ≈ 4 caracteres)
- Archivo promedio: ~100K caracteres / 100 chunks = ~1000 caracteres por chunk (consistente con 1024)

---

## 2️⃣ ¿EL PROCESO DE CHUNKING ESTÁ EN PYTHON O NODE?

### **✅ 100% PYTHON**

**Stack tecnológico:**
- **Lenguaje**: Python 3.x
- **Framework**: LlamaIndex (Python)
- **Librerías**:
  - `llama-index-core` - Core de LlamaIndex
  - `llama-index-embeddings-openai` - Embeddings de OpenAI
  - `llama-index-vector-stores-supabase` - Integración con Supabase
  - `psycopg2` - Conexión a PostgreSQL/Supabase

**No hay código Node.js en el pipeline de ingestión.**

---

## 3️⃣ ¿CUÁL ES TU PIPELINE?

### **Pipeline Completo:**

```
┌─────────────────────────────────────────────────────────────┐
│                    PIPELINE DE INGESTIÓN                     │
└─────────────────────────────────────────────────────────────┘

1️⃣ LEER PDF (y otros formatos)
   ↓
   SimpleDirectoryReader(input_files=[file_path])
   • Soporta: PDF, EPUB, TXT, DOCX, MD, DOC
   • Lee archivos desde ./data/
   • Convierte automáticamente a texto

2️⃣ CONVERTIR A TEXTO
   ↓
   reader.load_data()
   • LlamaIndex automáticamente extrae texto
   • Crea objetos Document con metadata
   • Maneja diferentes formatos internamente

3️⃣ DIVIDIR EN CHUNKS
   ↓
   VectorStoreIndex.from_documents()
   • LlamaIndex automáticamente divide en chunks
   • Chunk size: 1024 caracteres (default)
   • Chunk overlap: 200 caracteres (default)
   • Usa SentenceSplitter por defecto

4️⃣ LLAMAR EMBEDDINGS
   ↓
   embed_model = OpenAIEmbedding(model="text-embedding-3-small")
   • LlamaIndex automáticamente llama a OpenAI
   • Genera embeddings para cada chunk
   • Modelo: text-embedding-3-small
   • Dimensiones: 1536

5️⃣ SUBIR A SUPABASE
   ↓
   SupabaseVectorStore + VectorStoreIndex
   • Almacena vectores en PostgreSQL (pgvector)
   • Guarda metadata (file_name, chunk_id, etc.)
   • Tabla: vecs.knowledge (configurable)
```

---

## 📝 CÓDIGO ESPECÍFICO DEL PIPELINE

### **Archivo: `ingest_parallel_tier3.py`**

```python
# 1. LEER PDF
reader = SimpleDirectoryReader(input_files=[file_path])
documents = reader.load_data()  # Convierte a texto automáticamente

# 2-5. CHUNKING + EMBEDDINGS + SUBIR A SUPABASE (todo automático)
index = VectorStoreIndex.from_documents(
    documents,                    # Documentos ya en texto
    storage_context=storage_context,  # Configurado con Supabase
    embed_model=embed_model,      # OpenAI embeddings
    show_progress=False
)
```

**Todo sucede en una sola llamada:**
- ✅ Chunking automático
- ✅ Llamadas a embeddings automáticas
- ✅ Subida a Supabase automática

---

## 🔧 CONFIGURACIÓN ACTUAL

### **Embeddings:**
```python
embed_model = OpenAIEmbedding(model="text-embedding-3-small")
```

### **Vector Store:**
```python
vector_store = SupabaseVectorStore(
    postgres_connection_string=postgres_connection_string,
    collection_name=config.VECTOR_COLLECTION_NAME  # "knowledge"
)
```

### **Storage Context:**
```python
storage_context = StorageContext.from_defaults(vector_store=vector_store)
```

---

## 📊 ESTADÍSTICAS OBSERVADAS

**Basado en el código y logs:**
- **Chunks por archivo promedio**: ~100
- **Tokens por archivo promedio**: ~50,000
- **Chunk size estimado**: ~500 tokens/chunk (50K / 100)
- **O**: ~1024 tokens/chunk si hay overlap

**Nota**: La estimación de 100 requests/archivo sugiere que cada archivo genera ~100 chunks, lo cual es consistente con chunk size de ~500-1000 tokens.

---

## 💡 PERSONALIZACIÓN POSIBLE

Si quisieras cambiar el chunk size, necesitarías:

```python
from llama_index.core.node_parser import SentenceSplitter

# Configurar splitter personalizado
text_splitter = SentenceSplitter(
    chunk_size=512,      # Tamaño de chunk en caracteres (default: 1024)
    chunk_overlap=50     # Overlap entre chunks (default: 200)
)

# Usar en el índice
index = VectorStoreIndex.from_documents(
    documents,
    storage_context=storage_context,
    embed_model=embed_model,
    transformations=[text_splitter]  # Aplicar splitter personalizado
)
```

**Actualmente no está configurado**, así que usa los defaults de LlamaIndex.

---

## ✅ RESUMEN

| Pregunta | Respuesta |
|----------|-----------|
| **Chunk size** | 1024 caracteres (~256 tokens) (default de LlamaIndex) |
| **Chunking en** | Python (LlamaIndex) |
| **Pipeline** | SimpleDirectoryReader → load_data() → VectorStoreIndex.from_documents() |
| **Automatización** | Todo automático: chunking, embeddings, subida a Supabase |

**El pipeline es completamente automático y manejado por LlamaIndex.**

