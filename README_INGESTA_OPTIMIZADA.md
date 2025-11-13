# 🚀 PIPELINE DE INGESTA RAG OPTIMIZADO

## 📋 Descripción

Pipeline de ingesta optimizado para sistemas RAG que procesa documentos (PDFs, EPUBs, etc.) y los indexa en Supabase usando embeddings de OpenAI.

## ⚙️ Configuración

### Variables de Entorno

Crea un archivo `.env` con las siguientes variables:

```env
# Supabase
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_SERVICE_KEY=tu-service-key
SUPABASE_DB_PASSWORD=tu-password

# OpenAI
OPENAI_API_KEY=tu-api-key

# Configuración opcional (valores por defecto mostrados)
MAX_WORKERS=15
EMBEDDING_BATCH_SIZE=30
CHUNK_SIZE=1024
CHUNK_OVERLAP=200
OPENAI_RPM_TARGET=3500
OPENAI_TPM_TARGET=3500000
LOG_LEVEL=INFO
```

### Parámetros Configurables

| Parámetro | Default | Descripción |
|-----------|---------|-------------|
| `MAX_WORKERS` | 15 | Número de workers paralelos |
| `EMBEDDING_BATCH_SIZE` | 30 | Chunks por request a OpenAI (30-40) |
| `CHUNK_SIZE` | 1024 | Tamaño de chunk en caracteres |
| `CHUNK_OVERLAP` | 200 | Overlap entre chunks en caracteres |
| `OPENAI_RPM_TARGET` | 3500 | RPM objetivo (70% de 5000) |
| `OPENAI_TPM_TARGET` | 3500000 | TPM objetivo (70% de 5M) |
| `LOG_LEVEL` | INFO | Nivel de logging (DEBUG, INFO, WARNING, ERROR) |

## 🚀 Uso

### Ejecución Básica

```bash
python ingest_optimized_rag.py
```

### Ejecución con Configuración Personalizada

```bash
MAX_WORKERS=20 EMBEDDING_BATCH_SIZE=35 python ingest_optimized_rag.py
```

## 📊 Pipeline

El pipeline sigue estos pasos:

1. **Leer PDF/archivo**: Usa `SimpleDirectoryReader` de LlamaIndex
2. **Extraer texto**: Conversión automática a texto
3. **Dividir en chunks**: `SentenceSplitter` con 1024 caracteres y 200 de overlap
4. **Enviar embeddings**: Lotes de 30-40 chunks a OpenAI
5. **Guardar en Supabase**: Vectores y metadatos en pgvector

## 📈 Características

- ✅ **Control de rate limits**: Respeta límites de OpenAI Tier 3 (70% de capacidad)
- ✅ **Procesamiento paralelo**: 15 workers por defecto
- ✅ **Manejo robusto de errores**: Backoff exponencial para errores 429
- ✅ **Logging detallado**: Archivos procesados, errores, estadísticas
- ✅ **Reporte final**: Resumen completo al terminar
- ✅ **Detección de archivos sospechosos**: Archivos con menos de 5 chunks

## 📝 Reporte Final

Al terminar, se genera un reporte con:

- Número de archivos procesados (exitosos y fallidos)
- Total de chunks generados
- Tiempo total y promedio por archivo
- Lista de archivos sospechosos (< 5 chunks)
- Lista de archivos fallidos
- Estadísticas de uso de RPM/TPM

El reporte se guarda en: `reporte_ingesta_YYYYMMDD_HHMMSS.txt`

## 🔍 Logs

Los logs se guardan en:
- **Archivo**: `ingesta.log` (configurable con `LOG_FILE`)
- **Consola**: Salida estándar

## ⚠️ Notas Importantes

- **NO cambiar chunk size u overlap** sin solicitud explícita (reglas de arquitectura)
- **NO cambiar modelo de embeddings** sin solicitud explícita
- **NO exceder 70% de límites de Tier 3** (3,500 RPM, 3,500,000 TPM)
- Los archivos se procesan desde `./data/` (configurable en `config.py`)

## 🐛 Troubleshooting

### Error: "Faltan variables de entorno"
- Verifica que el archivo `.env` exista y contenga todas las variables necesarias

### Error: "Rate limit exceeded"
- El sistema debería manejar esto automáticamente con backoff exponencial
- Si persiste, reduce `MAX_WORKERS` o `EMBEDDING_BATCH_SIZE`

### Archivos sospechosos
- Archivos con menos de 5 chunks pueden indicar problemas de extracción
- Revisa manualmente estos archivos

## 📚 Archivos Relacionados

- `.cursor/rules/rag_ingesta.md`: Reglas de arquitectura
- `config_ingesta.py`: Configuración centralizada
- `config.py`: Configuración del proyecto general

