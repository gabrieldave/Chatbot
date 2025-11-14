# ✅ INGESTA REANUDADA CON CONFIGURACIÓN REDUCIDA

## 🔧 Configuración Aplicada

### Cambios Realizados:

1. **Workers reducidos**: 15 → **5 workers**
2. **Batch size reducido**: 30 → **20 chunks por batch**
3. **RPM Target reducido**: 3,500 → **~2,850 RPM** (57% en lugar de 70%)
4. **TPM Target reducido**: 3,500,000 → **~2,850,000 TPM** (57% en lugar de 70%)

### Proceso:
- ✅ **1 solo proceso** ejecutándose (no 3 en paralelo)
- ✅ Configuración optimizada para evitar sobrecarga en Supabase

---

## 📊 Estado Actual

- **Proceso**: `ingest_optimized_rag.py` ejecutándose
- **Workers**: 5 (reducido de 15)
- **Batch size**: 20 (reducido de 30)
- **Velocidad**: Reducida para dar margen a Supabase

---

## ⚠️ Monitoreo Recomendado

### Verificar cada 15-30 minutos:

1. **Dashboard de Supabase**:
   - Memory libre > 200 MB
   - I/O Wait < 50%
   - IOPS estable

2. **Proceso de ingesta**:
   ```bash
   python verificar_estado_ingesta.py
   ```

3. **Workers**:
   ```bash
   python verificar_workers.py
   ```

---

## 🛑 Detener si:

- Memory libre < 100 MB
- I/O Wait > 80%
- Queries bloqueadas > 1 minuto
- Errores de conexión frecuentes

---

## 📈 Progreso

- **Chunks actuales**: ~506,539
- **Archivos estimados**: ~5,065
- **Tamaño BD**: 5.05 GB / 8 GB (63%)

---

**✅ Ingesta reanudada con configuración segura para Supabase**



