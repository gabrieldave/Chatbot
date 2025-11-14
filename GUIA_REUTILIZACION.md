# 🔄 GUÍA DE REUTILIZACIÓN DE LA INFRAESTRUCTURA RAG

## 📋 Visión General

Esta infraestructura RAG está diseñada para ser **completamente reutilizable** en diferentes proyectos. Puedes usarla para:

- Indexar documentos en cualquier proyecto
- Crear sistemas RAG personalizados
- Integrar búsqueda semántica en aplicaciones
- Procesar y analizar grandes volúmenes de documentos

---

## 🏗️ Estructura Modular

La infraestructura está organizada en módulos independientes:

```
rag_infrastructure/
├── __init__.py              # Exportaciones principales
├── pipeline.py              # Pipeline principal
├── config.py                # Configuración
├── ingestion.py             # Motor de ingesta
├── monitor.py               # Monitor y reportes
├── anti_duplicates.py       # Sistema anti-duplicados
├── metadata_extractor.py    # Extracción de metadatos
├── error_logger.py          # Logging de errores
└── rag_search.py            # Búsqueda con filtros
```

Cada módulo puede usarse **independientemente** o como parte del pipeline completo.

---

## 🚀 Uso Básico: Pipeline Completo

### Instalación

1. Copia la carpeta `rag_infrastructure/` a tu proyecto
2. Instala dependencias:
   ```bash
   pip install llama-index openai psycopg2-binary python-dotenv
   ```

### Ejemplo Mínimo

```python
from rag_infrastructure import RAGIngestionPipeline

# Crear pipeline
pipeline = RAGIngestionPipeline(
    data_directory="./documents",
    supabase_url="https://xxx.supabase.co",
    supabase_password="tu_password",
    openai_api_key="sk-..."
)

# Ejecutar ingesta
results = pipeline.ingest()

# Realizar búsqueda
resultados = pipeline.search(
    query="¿Qué es machine learning?",
    language="es",
    category="tecnología"
)
```

---

## 🔧 Uso Avanzado: Módulos Individuales

### 1. Solo Extracción de Metadatos

```python
from rag_infrastructure.metadata_extractor import extract_rich_metadata

metadata = extract_rich_metadata(
    file_path="./documento.pdf",
    text="Texto extraído del documento..."
)

print(f"Título: {metadata['title']}")
print(f"Autor: {metadata['author']}")
print(f"Idioma: {metadata['language']}")
print(f"Categoría: {metadata['category']}")
```

### 2. Solo Sistema Anti-Duplicados

```python
from rag_infrastructure.anti_duplicates import (
    calculate_doc_id,
    check_document_exists,
    register_document
)

# Calcular ID único
doc_id = calculate_doc_id("./documento.pdf")

# Verificar si existe
exists, doc_info = check_document_exists(doc_id)

if not exists:
    # Registrar nuevo documento
    register_document(
        doc_id=doc_id,
        filename="documento.pdf",
        file_path="./documento.pdf",
        title="Mi Documento",
        author="Autor",
        language="es",
        category="general"
    )
```

### 3. Solo Búsqueda con Filtros

```python
from rag_infrastructure.rag_search import search_with_filters

resultados = search_with_filters(
    query="estrategias de inversión",
    top_k=10,
    language="es",
    category="finanzas",
    year_min=2020
)

for resultado in resultados:
    print(f"Título: {resultado['document_info']['title']}")
    print(f"Contenido: {resultado['content'][:200]}...")
```

### 4. Solo Logging de Errores

```python
from rag_infrastructure.error_logger import log_error, ErrorType

try:
    # Tu código aquí
    process_document()
except Exception as e:
    log_error(
        filename="documento.pdf",
        error_type=ErrorType.EXTRACTION_ERROR,
        error_message=str(e),
        exception=e
    )
```

---

## 🎯 Casos de Uso Comunes

### Caso 1: Sistema de Documentación Técnica

```python
pipeline = RAGIngestionPipeline(
    data_directory="./docs",
    supabase_url="...",
    supabase_password="...",
    openai_api_key="...",
    collection_name="technical_docs"
)

# Indexar documentación
pipeline.ingest()

# Buscar en documentación
resultados = pipeline.search(
    query="cómo usar la API",
    category="documentación"
)
```

### Caso 2: Biblioteca de Libros

```python
pipeline = RAGIngestionPipeline(
    data_directory="./libros",
    supabase_url="...",
    supabase_password="...",
    openai_api_key="...",
    collection_name="library"
)

# Indexar libros
pipeline.ingest()

# Buscar por autor y año
resultados = pipeline.search(
    query="psicología positiva",
    author="Seligman",
    year_min=2010
)
```

### Caso 3: Base de Conocimiento Empresarial

```python
pipeline = RAGIngestionPipeline(
    data_directory="./knowledge_base",
    supabase_url="...",
    supabase_password="...",
    openai_api_key="...",
    collection_name="company_kb"
)

# Indexar documentos internos
pipeline.ingest()

# Buscar por departamento (categoría)
resultados = pipeline.search(
    query="políticas de recursos humanos",
    category="RRHH"
)
```

---

## 🔌 Integración con Otros Frameworks

### Con FastAPI

```python
from fastapi import FastAPI
from rag_infrastructure import RAGIngestionPipeline

app = FastAPI()
pipeline = RAGIngestionPipeline(...)

@app.post("/ingest")
async def ingest_documents():
    results = pipeline.ingest()
    return results

@app.get("/search")
async def search(query: str, language: str = None):
    resultados = pipeline.search(query=query, language=language)
    return resultados
```

### Con Flask

```python
from flask import Flask, request, jsonify
from rag_infrastructure import RAGIngestionPipeline

app = Flask(__name__)
pipeline = RAGIngestionPipeline(...)

@app.route('/search', methods=['POST'])
def search():
    data = request.json
    resultados = pipeline.search(
        query=data['query'],
        language=data.get('language'),
        category=data.get('category')
    )
    return jsonify(resultados)
```

### Con Django

```python
# views.py
from django.http import JsonResponse
from rag_infrastructure import RAGIngestionPipeline

pipeline = RAGIngestionPipeline(...)

def search_view(request):
    query = request.GET.get('query')
    resultados = pipeline.search(query=query)
    return JsonResponse({'results': resultados})
```

---

## ⚙️ Configuración Personalizada

### Variables de Entorno

Crea un archivo `.env`:

```env
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_DB_PASSWORD=tu_password
OPENAI_API_KEY=sk-...
DATA_DIRECTORY=./documents
COLLECTION_NAME=knowledge
CHUNK_SIZE=1024
CHUNK_OVERLAP=200
EMBEDDING_BATCH_SIZE=30
MAX_WORKERS=15
```

### Configuración Programática

```python
from rag_infrastructure import RAGIngestionPipeline

pipeline = RAGIngestionPipeline(
    data_directory="./custom_docs",
    supabase_url="...",
    supabase_password="...",
    openai_api_key="...",
    # Personalizar
    chunk_size=2048,           # Chunks más grandes
    chunk_overlap=400,          # Más overlap
    embedding_batch_size=50,    # Batches más grandes
    max_workers=20,             # Más workers
    embedding_model="text-embedding-3-large"  # Modelo diferente
)
```

---

## 📦 Empaquetado para Distribución

### Crear Paquete Instalable

Crea `setup.py`:

```python
from setuptools import setup, find_packages

setup(
    name="rag-infrastructure",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "llama-index",
        "openai",
        "psycopg2-binary",
        "python-dotenv",
    ],
    extras_require={
        "metadata": ["PyPDF2", "langdetect"],
    }
)
```

Instalar:
```bash
pip install -e .
```

---

## 🔄 Migración de Proyectos Existentes

### Paso 1: Copiar Infraestructura

```bash
cp -r rag_infrastructure/ /ruta/nuevo/proyecto/
```

### Paso 2: Adaptar Configuración

```python
# En tu nuevo proyecto
from rag_infrastructure import RAGIngestionPipeline

# Usar tu configuración existente
pipeline = RAGIngestionPipeline(
    data_directory=TU_DATA_DIR,
    supabase_url=TU_SUPABASE_URL,
    supabase_password=TU_PASSWORD,
    openai_api_key=TU_API_KEY
)
```

### Paso 3: Migrar Datos (si es necesario)

Si ya tienes datos indexados, la infraestructura los detectará automáticamente gracias al sistema anti-duplicados.

---

## 🎨 Personalización Avanzada

### Extender Extracción de Metadatos

```python
from rag_infrastructure.metadata_extractor import extract_rich_metadata

def custom_metadata_extractor(file_path, text):
    # Tu lógica personalizada
    metadata = extract_rich_metadata(file_path, text)
    
    # Agregar campos personalizados
    metadata['custom_field'] = "valor"
    
    return metadata
```

### Agregar Nuevas Categorías

```python
from rag_infrastructure.metadata_extractor import classify_category

# Modificar la función classify_category para agregar nuevas categorías
# O crear tu propia función de clasificación
```

### Personalizar Búsqueda

```python
from rag_infrastructure.rag_search import search_with_filters

def custom_search(query, **filters):
    # Tu lógica personalizada antes de buscar
    preprocessed_query = preprocess(query)
    
    # Usar búsqueda estándar
    resultados = search_with_filters(preprocessed_query, **filters)
    
    # Post-procesar resultados
    return postprocess(resultados)
```

---

## 📊 Monitoreo y Reportes

El pipeline incluye monitor y reportes automáticos:

```python
pipeline = RAGIngestionPipeline(...)
results = pipeline.ingest()

# El reporte se genera automáticamente
# Se guarda en: ingestion_report_YYYYMMDD_HHMMSS.md

# También puedes acceder a estadísticas
stats = pipeline.monitor.get_stats()
print(f"Archivos procesados: {stats.files_processed}")
print(f"Chunks generados: {stats.total_chunks}")
```

---

## 🐛 Debugging y Troubleshooting

### Ver Logs de Errores

```python
from rag_infrastructure.error_logger import get_error_summary, get_recent_errors

# Resumen de errores
summary = get_error_summary()
print(f"Total errores: {summary['total_errors']}")

# Errores recientes
recent = get_recent_errors(limit=10)
for error in recent:
    print(f"{error['filename']}: {error['error_type']}")
```

### Verificar Estado de Tablas

```python
from rag_infrastructure.anti_duplicates import ensure_documents_table
from rag_infrastructure.error_logger import ensure_errors_table

# Verificar/crear tablas
ensure_documents_table()
ensure_errors_table()
```

---

## ✅ Checklist de Reutilización

- [ ] Copiar carpeta `rag_infrastructure/` al nuevo proyecto
- [ ] Instalar dependencias (`pip install ...`)
- [ ] Configurar variables de entorno (`.env`)
- [ ] Crear instancia de `RAGIngestionPipeline`
- [ ] Ejecutar `pipeline.ingest()`
- [ ] Probar búsquedas con `pipeline.search()`
- [ ] Personalizar según necesidades
- [ ] Integrar con tu aplicación (FastAPI, Flask, etc.)

---

## 🎉 ¡Listo!

Tu infraestructura RAG está lista para ser reutilizada en cualquier proyecto. Es modular, extensible y completamente funcional.

**¿Necesitas ayuda?** Revisa los ejemplos en `EJEMPLO_BUSQUEDA_FILTROS.py` y `EJEMPLO_ERROR_LOGGING.md`.

