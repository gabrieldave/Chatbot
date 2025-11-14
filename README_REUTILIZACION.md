# 🔄 INFRAESTRUCTURA RAG REUTILIZABLE

## 🎯 ¿Qué es esto?

Esta es una **infraestructura RAG completa y reutilizable** que puedes usar en cualquier proyecto que necesite:

- ✅ Indexar documentos (PDFs, textos, etc.)
- ✅ Búsqueda semántica con filtros
- ✅ Sistema anti-duplicados robusto
- ✅ Extracción automática de metadatos
- ✅ Logging profesional de errores
- ✅ Monitor y reportes en tiempo real

## 🚀 Inicio Rápido

### 1. Copiar la Infraestructura

```bash
# Copia la carpeta rag_infrastructure/ a tu nuevo proyecto
cp -r rag_infrastructure/ /ruta/tu/proyecto/
```

### 2. Instalar Dependencias

```bash
pip install llama-index openai psycopg2-binary python-dotenv
```

### 3. Configurar Variables de Entorno

Crea un archivo `.env`:

```env
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_DB_PASSWORD=tu_password
OPENAI_API_KEY=sk-...
DATA_DIRECTORY=./documents
```

### 4. Usar en tu Código

```python
from rag_infrastructure import RAGIngestionPipeline

pipeline = RAGIngestionPipeline(
    data_directory="./documents",
    supabase_url="https://xxx.supabase.co",
    supabase_password="tu_password",
    openai_api_key="sk-..."
)

# Indexar documentos
pipeline.ingest()

# Buscar
resultados = pipeline.search(
    query="¿Qué es machine learning?",
    language="es"
)
```

## 📚 Documentación Completa

Ver `GUIA_REUTILIZACION.md` para:
- Uso avanzado
- Integración con APIs
- Personalización
- Casos de uso
- Ejemplos completos

## 🎨 Características

- ✅ **Modular**: Usa solo lo que necesites
- ✅ **Configurable**: Ajusta todos los parámetros
- ✅ **Robusto**: Manejo de errores completo
- ✅ **Escalable**: Procesamiento paralelo
- ✅ **Profesional**: Logging y reportes detallados

## 📦 Estructura

```
rag_infrastructure/
├── __init__.py              # Exportaciones principales
├── pipeline.py              # Pipeline principal
├── config.py                # Configuración
├── ingestion.py             # Motor de ingesta
├── monitor.py               # Monitor y reportes
├── anti_duplicates.py       # Anti-duplicados
├── metadata_extractor.py   # Metadatos
├── error_logger.py          # Logging
└── rag_search.py            # Búsqueda
```

## 🔧 Módulos Disponibles

- **RAGIngestionPipeline**: Pipeline completo
- **extract_rich_metadata**: Extracción de metadatos
- **search_with_filters**: Búsqueda con filtros
- **log_error**: Logging de errores
- **calculate_doc_id**: IDs únicos

## 📖 Ejemplos

Ver `EJEMPLO_PROYECTO_NUEVO.py` para ejemplos completos de:
- Uso simple
- Uso modular
- Integración con FastAPI
- Procesamiento por lotes
- Configuración personalizada

## ✅ Checklist de Reutilización

- [ ] Copiar `rag_infrastructure/` al nuevo proyecto
- [ ] Instalar dependencias
- [ ] Configurar `.env`
- [ ] Crear instancia de `RAGIngestionPipeline`
- [ ] Ejecutar `pipeline.ingest()`
- [ ] Probar búsquedas
- [ ] Personalizar según necesidades

## 🎉 ¡Listo!

Tu infraestructura RAG está lista para ser reutilizada en cualquier proyecto.

