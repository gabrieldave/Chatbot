# 🔴 EJEMPLO DE ENTRADA EN TABLA `ingestion_errors`

## Estructura de la Tabla

```sql
CREATE TABLE ingestion_errors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_id TEXT,
    filename TEXT NOT NULL,
    error_type TEXT NOT NULL,
    error_message TEXT NOT NULL,
    traceback TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Ejemplo de Entrada

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "doc_id": "3f8a9b2c1d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a",
  "filename": "libro_corrupto.pdf",
  "error_type": "PDF_PARSE_ERROR",
  "error_message": "No se pudo leer el PDF: archivo corrupto o protegido con contraseña",
  "traceback": "Traceback (most recent call last):\n  File \"ingest_optimized_rag.py\", line 426, in process_single_file\n    documents = extract_text_from_file(file_path)\n  File \"ingest_optimized_rag.py\", line 250, in extract_text_from_file\n    raise Exception(f\"Error extrayendo texto: {e}\")\nException: No se pudo leer el PDF: archivo corrupto",
  "created_at": "2025-01-15 14:30:45.123456+00"
}
```

## Tipos de Errores Registrados

### 1. PDF_PARSE_ERROR
```json
{
  "error_type": "PDF_PARSE_ERROR",
  "error_message": "No se pudo parsear el PDF: formato no válido",
  "doc_id": "abc123...",
  "filename": "documento.pdf"
}
```

### 2. EXTRACTION_ERROR
```json
{
  "error_type": "EXTRACTION_ERROR",
  "error_message": "Sin contenido extraído del archivo",
  "doc_id": "def456...",
  "filename": "archivo_vacio.txt"
}
```

### 3. CHUNKING_ERROR
```json
{
  "error_type": "CHUNKING_ERROR",
  "error_message": "Error dividiendo en chunks: texto demasiado corto",
  "doc_id": "ghi789...",
  "filename": "nota_corta.txt"
}
```

### 4. OPENAI_ERROR
```json
{
  "error_type": "OPENAI_ERROR",
  "error_message": "Error en API de OpenAI: Invalid API key",
  "doc_id": "jkl012...",
  "filename": "libro.pdf"
}
```

### 5. RATE_LIMIT_ERROR
```json
{
  "error_type": "RATE_LIMIT_ERROR",
  "error_message": "Rate limit exceeded: 429 Too Many Requests",
  "doc_id": "mno345...",
  "filename": "documento_largo.pdf"
}
```

### 6. SUPABASE_ERROR
```json
{
  "error_type": "SUPABASE_ERROR",
  "error_message": "Error insertando en Supabase: connection timeout",
  "doc_id": "pqr678...",
  "filename": "archivo.pdf"
}
```

### 7. NETWORK_ERROR
```json
{
  "error_type": "NETWORK_ERROR",
  "error_message": "Error de red: connection refused",
  "doc_id": "stu901...",
  "filename": "libro.pdf"
}
```

### 8. METADATA_ERROR
```json
{
  "error_type": "METADATA_ERROR",
  "error_message": "Error extrayendo metadatos: langdetect no disponible",
  "doc_id": "vwx234...",
  "filename": "documento.pdf"
}
```

### 9. HASH_ERROR
```json
{
  "error_type": "HASH_ERROR",
  "error_message": "Error calculando hash del archivo: archivo no encontrado",
  "doc_id": null,
  "filename": "archivo_inexistente.pdf"
}
```

## Consultas Útiles

### Obtener todos los errores de un archivo
```sql
SELECT * FROM ingestion_errors 
WHERE filename = 'libro_corrupto.pdf'
ORDER BY created_at DESC;
```

### Contar errores por tipo
```sql
SELECT error_type, COUNT(*) as count
FROM ingestion_errors
GROUP BY error_type
ORDER BY count DESC;
```

### Obtener errores recientes
```sql
SELECT filename, error_type, error_message, created_at
FROM ingestion_errors
ORDER BY created_at DESC
LIMIT 20;
```

### Obtener archivos con más errores
```sql
SELECT filename, COUNT(*) as error_count
FROM ingestion_errors
GROUP BY filename
ORDER BY error_count DESC
LIMIT 10;
```

