# 🚨 RESUMEN: EMERGENCIA SUPABASE - PROCESOS DETENIDOS

## ⚠️ Situación Detectada

Basado en el dashboard de Supabase que compartiste:

### Problemas Críticos:
- **Memory**: Solo 77.95 MB libre de 1.8 GB total (95.7% usado) 🔴
- **CPU I/O Wait**: 75.87% (sobrecarga de disco) 🔴
- **Base de datos**: 5.05 GB / 8 GB (63%, pero creciendo rápidamente) ⚠️
- **IOPS**: 751.96 / 3000 (25%, pero con mucho I/O wait)

### Estado de Procesos:
- **3 procesos de ingesta** activos
- **45 workers totales** (15 por proceso)
- **CPU total**: ~273% (muy alto)
- **RAM total**: ~7.75 GB

---

## ✅ Acción Tomada

**Todos los procesos de ingesta han sido detenidos** para aliviar la carga en Supabase.

### Procesos Detenidos:
- ✅ PID 13128 - `ingest_parallel_tier3.py`
- ✅ PID 25216 - `ingest_parallel_tier3.py`
- ✅ PID 33040 - `ingest_parallel_tier3.py`

---

## 📊 Progreso Hasta el Momento

- **Chunks indexados**: ~506,539
- **Archivos estimados**: ~5,065
- **Tamaño de BD**: 5.05 GB / 8 GB (63%)

---

## 🔧 Configuración Recomendada para Reanudar

### Cambios Necesarios en `config_ingesta.py`:

```python
# Workers reducidos (de 15 a 5)
MAX_WORKERS = 5

# Batch size reducido (de 30 a 20)
EMBEDDING_BATCH_SIZE = 20

# Rate limits reducidos
OPENAI_RPM_TARGET = 2000  # De 3500
OPENAI_TPM_TARGET = 2000000  # De 3500000
```

### Ejecución Recomendada:

1. **Solo 1 proceso** (no 3 procesos en paralelo)
2. **Workers reducidos**: 5 en lugar de 15
3. **Batch size reducido**: 20 en lugar de 30
4. **Monitoreo constante** del dashboard de Supabase

---

## ⏳ Próximos Pasos

### Inmediato (Ahora):
1. ✅ Procesos detenidos
2. ⏳ Esperar 5-10 minutos para que Supabase se estabilice
3. 📊 Verificar dashboard de Supabase:
   - Memory debe aumentar (más libre)
   - I/O Wait debe disminuir
   - IOPS debe estabilizarse

### Antes de Reanudar:
1. Verificar que Supabase esté estable:
   - Memory libre > 500 MB
   - I/O Wait < 30%
   - No hay queries bloqueadas

2. Aplicar configuración reducida:
   ```bash
   # Editar config_ingesta.py con valores reducidos
   # O usar el archivo config_ingesta_reducida.py como referencia
   ```

3. Ejecutar solo 1 proceso:
   ```bash
   python ingest_optimized_rag.py
   # NO ejecutar múltiples procesos en paralelo
   ```

### Monitoreo Continuo:
- Verificar dashboard cada 15-30 minutos
- Si Memory baja de 200 MB libre → Pausar
- Si I/O Wait > 50% → Reducir workers
- Si hay queries bloqueadas > 30s → Detener

---

## 📈 Estrategia de Reanudación Gradual

### Fase 1 (Inicial):
- 1 proceso
- 3 workers
- Batch size: 15
- Monitorear 30 minutos

### Fase 2 (Si estable):
- 1 proceso
- 5 workers
- Batch size: 20
- Monitorear 1 hora

### Fase 3 (Si muy estable):
- 1 proceso
- 8 workers
- Batch size: 25
- Monitorear continuamente

**NO volver a 15 workers ni 3 procesos hasta que Supabase esté completamente estable.**

---

## 🔍 Scripts de Verificación

```bash
# Verificar estado de Supabase
python verificar_limites_supabase.py

# Verificar procesos activos
python verificar_estado_ingesta.py

# Contar indexados
python contar_final.py
```

---

## ⚠️ Señales de Alerta

Detener inmediatamente si:
- Memory libre < 100 MB
- I/O Wait > 80%
- Queries bloqueadas > 1 minuto
- Errores de conexión frecuentes
- Timeouts en queries

---

## ✅ Estado Actual

- ✅ Procesos detenidos
- ⏳ Esperando estabilización de Supabase
- 📊 Monitoreo recomendado antes de reanudar

**Espera al menos 10 minutos antes de reanudar la ingesta.**



