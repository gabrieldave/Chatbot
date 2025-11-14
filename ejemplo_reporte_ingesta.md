# 📊 Reporte de Ingesta RAG

**Fecha de generación**: 2025-11-13 14:30:45

---

## 📅 Información de Ejecución

- **Fecha y hora de inicio**: 2025-11-13 13:15:30
- **Fecha y hora de finalización**: 2025-11-13 14:30:45
- **Tiempo total de ejecución**: 1h 15m 15s

---

## 📈 Resumen General

| Métrica | Valor |
|---------|-------|
| **Archivos totales** | 1,218 |
| **Archivos procesados correctamente** | 1,195 |
| **Archivos con errores** | 3 |
| **Archivos sospechosos** (< 5 chunks) | 5 |
| **Chunks totales generados** | 128,245 |
| **Promedio de chunks por archivo** | 107.3 |
| **Mínimo de chunks por archivo** | 2 |
| **Máximo de chunks por archivo** | 1,245 |

---

## ⚠️ Advertencias y Problemas

### Archivos Sospechosos (< 5 chunks)

- `libro_corto.pdf` (2 chunks)
- `resumen.txt` (3 chunks)
- `notas.md` (4 chunks)
- `introduccion.pdf` (3 chunks)
- `prefacio.epub` (4 chunks)

### Archivos con Error Total

- `archivo_corrupto.pdf`
  - Error: No se pudo extraer texto del PDF
  - Tipo: extraction
  - Timestamp: 2025-11-13T13:45:12

- `documento_protegido.pdf`
  - Error: PDF protegido con contraseña
  - Tipo: extraction
  - Timestamp: 2025-11-13T14:10:33

- `archivo_vacio.txt`
  - Error: Archivo vacío o sin contenido válido
  - Tipo: extraction
  - Timestamp: 2025-11-13T14:25:01

---

## ⚡ Métricas de Rendimiento

| Métrica | Valor |
|---------|-------|
| **Velocidad promedio (archivos/minuto)** | 15.87 |
| **Velocidad promedio (chunks/minuto)** | 1,703 |
| **RPM estimado promedio** | 3,245 / 3,500 (92.7%) |
| **TPM estimado promedio** | 3,280,000 / 3,500,000 (93.7%) |

---

## 🔄 Notas de Ejecución

- **Reintentos por rate limit (429)**: 12
- **Errores de red**: 2
- **Otros errores**: 1
- **Total de errores**: 15

---

## 📊 Distribución de Chunks por Archivo

| Rango de Chunks | Número de Archivos |
|-----------------|-------------------|
| 0-5 (sospechosos) | 5 |
| 5-20 | 23 |
| 20-50 | 187 |
| 50-100 | 456 |
| 100-200 | 398 |
| 200+ | 126 |

---

## ✅ Conclusión

✅ **Ingesta completada exitosamente con algunas advertencias menores.**

- **Tasa de éxito**: 98.1%
- **Chunks promedio por archivo**: 107.3
- **Uso de capacidad OpenAI**: 92.7% RPM, 93.7% TPM

**Recomendaciones:**
- Revisar manualmente los 5 archivos sospechosos (< 5 chunks)
- Verificar los 3 archivos que fallaron completamente
- El sistema operó cerca del límite objetivo (70%), considerando reducir workers si se desea más margen

---

*Reporte generado automáticamente por el sistema de ingesta RAG*



