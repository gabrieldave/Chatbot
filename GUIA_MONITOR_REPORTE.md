# 📊 Guía del Monitor y Reporte de Ingesta

## 🎯 Características Implementadas

### 1. Monitor en Tiempo Real

El monitor (`ingestion_monitor.py`) proporciona:

- ✅ **Actualizaciones periódicas** cada 5 segundos (configurable)
- ✅ **Visualización con rich** (si está instalado) o salida simple
- ✅ **Métricas en tiempo real**:
  - Progreso (%)
  - Velocidad (archivos/min, chunks/min)
  - ETA (tiempo estimado restante)
  - RPM/TPM estimados
  - Archivos completados/fallidos/sospechosos

### 2. Reporte Final Detallado

El reporte incluye:

- ✅ **Información de ejecución**: Fechas, tiempos
- ✅ **Resumen general**: Estadísticas completas
- ✅ **Advertencias**: Archivos sospechosos y fallidos
- ✅ **Métricas de rendimiento**: Velocidad, RPM, TPM
- ✅ **Distribución de chunks**: Tabla de rangos
- ✅ **Notas de ejecución**: Reintentos, errores
- ✅ **Conclusión**: Resumen y recomendaciones

## ⚙️ Configuración

### Variables de Entorno

```env
# Intervalo de actualización del monitor (segundos)
MONITOR_UPDATE_INTERVAL=5

# Número máximo de archivos problemáticos a listar en detalle
MAX_PROBLEMATIC_FILES_DETAIL=20

# Ruta y nombre del archivo de reporte (usar {timestamp} para timestamp)
REPORT_FILE_PATH=ingestion_report_{timestamp}.md
```

## 🚀 Uso

### Ejecución Normal

```bash
python ingest_optimized_rag.py
```

El monitor se iniciará automáticamente y mostrará actualizaciones cada 5 segundos.

### Con Configuración Personalizada

```bash
MONITOR_UPDATE_INTERVAL=10 MAX_PROBLEMATIC_FILES_DETAIL=50 python ingest_optimized_rag.py
```

## 📊 Salida del Monitor

### Con Rich (Recomendado)

Si tienes `rich` instalado (`pip install rich`), verás una tabla actualizada en tiempo real:

```
┌─────────────────────────────────────────────────────────┐
│           📊 Monitor de Ingesta RAG                     │
├─────────────────────────────────────────────────────────┤
│ 📚 Progreso          │ 950/1218 (77.9%)                │
│ ⏱️  Tiempo           │ 1h 15m 30s                       │
│ ⚡ Velocidad         │ 12.67 archivos/min │ 1,360 chunks/min │
│ 🎯 ETA               │ 0h 21m 10s                       │
│ 📦 Chunks totales    │ 102,080                          │
│ ✅ Completados       │ 950                              │
│ ❌ Fallidos          │ 2                                │
│ ⚠️  Sospechosos      │ 3                                │
│ 🔄 Reintentos (429)  │ 8                                │
│ 📊 RPM estimado      │ 3,120/3500 (89.1%)              │
│ 📊 TPM estimado      │ 2,980,000/3,500,000 (85.1%)     │
└─────────────────────────────────────────────────────────┘
```

### Sin Rich

Si no tienes `rich`, verás una salida simple pero clara:

```
================================================================================
📊 MONITOR DE INGESTA RAG - 14:30:15
================================================================================
📚 Progreso: 950/1218 (77.9%)
⏱️  Tiempo: 1h 15m 30s
⚡ Velocidad: 12.67 archivos/min | 1,360 chunks/min
🎯 ETA: 0h 21m 10s
📦 Chunks: 102,080
✅ Completados: 950 | ❌ Fallidos: 2 | ⚠️  Sospechosos: 3
🔄 Reintentos 429: 8
📊 RPM: 3,120/3500 (89.1%) | TPM: 2,980,000/3,500,000 (85.1%)
================================================================================
```

## 📄 Reporte Final

Al terminar, se genera un archivo markdown con el reporte completo. Ver `ejemplo_reporte_ingesta.md` para un ejemplo.

El reporte se guarda en:
- `ingestion_report_YYYYMMDD_HHMMSS.md` (por defecto)
- O el nombre especificado en `REPORT_FILE_PATH`

## 🔧 Integración en el Pipeline

El monitor se integra automáticamente en el pipeline:

1. **Inicio**: Se crea e inicia al comenzar la ingesta
2. **Durante procesamiento**: 
   - `on_file_started()`: Cuando un archivo comienza a procesarse
   - `on_file_completed()`: Cuando un archivo se completa
   - `on_file_error()`: Cuando hay un error
   - `on_chunk_batch_processed()`: Cuando se procesa un batch de chunks
   - `on_rate_limit_retry()`: Cuando hay un reintento por rate limit
3. **Finalización**: Se detiene y genera el reporte final

## 📝 Notas Técnicas

- El monitor es **thread-safe** usando locks
- Las métricas se actualizan en tiempo real
- El reporte se genera al finalizar el proceso
- Si `rich` no está disponible, funciona con salida simple

## 🐛 Troubleshooting

### El monitor no muestra actualizaciones
- Verifica que el proceso esté corriendo
- Revisa los logs para errores
- Aumenta `MONITOR_UPDATE_INTERVAL` si es necesario

### El reporte no se genera
- Verifica permisos de escritura en el directorio
- Revisa los logs para errores
- El reporte se genera al finalizar, espera a que termine el proceso

### Rich no funciona
- Instala con: `pip install rich`
- Si no está disponible, el sistema usa salida simple automáticamente

