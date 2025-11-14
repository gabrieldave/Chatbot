# 🔬 EXPERIMENTO: Aumento de RAM en Supabase

## 📋 Objetivo

Verificar si el margen de seguridad de RAM (~10%, 200 MB) es real o si había más capacidad disponible.

## 🎯 Hipótesis

**Si el margen es real:**
- Al aumentar RAM de 2 GB a 4 GB
- El uso de RAM debería aumentar proporcionalmente
- De ~1.8 GB (90% de 2 GB) a ~3.6 GB (90% de 4 GB)
- Esto confirmaría que había un límite real

**Si el margen NO era real:**
- Al aumentar RAM a 4 GB
- El uso se mantendría en ~1.8 GB
- Esto indicaría que había más capacidad disponible

## ⚙️ Configuración del Experimento

- **batch_size**: FIJADO en 15 (no cambiar durante el experimento)
- **RAM Supabase**: Aumentar de 2 GB a 4 GB
- **Monitoreo**: Observar uso de RAM en panel de Supabase

## 📊 Qué Observar

### Antes del aumento (2 GB RAM):
- Uso actual: ~1.8 GB (90%)
- batch_size: 15

### Después del aumento (4 GB RAM):
- **Escenario A - Margen real:**
  - Uso aumenta a ~3.6 GB (90% de 4 GB)
  - Confirma que había límite real
  - Podemos aumentar batch_size después

- **Escenario B - Margen no real:**
  - Uso se mantiene en ~1.8 GB
  - Indica que había más capacidad
  - Podemos ser más agresivos con batch_size

## 🔍 Cómo Ejecutar

1. **Verificar batch_size actual:**
   ```bash
   python check_progress_now.py
   ```
   Debe mostrar: `batch_size: 15`

2. **Iniciar monitoreo (opcional):**
   ```bash
   python monitor_ram_experiment.py
   ```

3. **Aumentar RAM en Supabase:**
   - Ir al panel de Supabase
   - Aumentar Compute de 2 GB a 4 GB
   - Esperar a que se reinicie (puede tomar unos minutos)

4. **Observar cambios:**
   - Verificar uso de RAM en el panel
   - Ver si aumenta o se mantiene
   - Monitorear progreso de indexación

## 📈 Resultados Esperados

### Si el uso aumenta (Escenario A):
✅ **Confirmado**: El margen de seguridad era real
- Podemos aumentar batch_size a 30-40 después
- Con 4 GB, podríamos usar batch_size de 60-80
- Velocidad aumentaría significativamente

### Si el uso se mantiene (Escenario B):
✅ **Confirmado**: Había más capacidad disponible
- Podemos aumentar batch_size inmediatamente
- El límite era más conservador de lo necesario
- Podemos ser más agresivos con 2 GB

## ⚠️ Notas Importantes

- El batch_size está **FIJO en 15** durante el experimento
- El monitor maestro seguirá corriendo pero no cambiará el batch_size
- El proceso de ingest continuará normalmente
- Después del experimento, ajustaremos según resultados

## 🎯 Siguiente Paso

Después de ver los resultados, ajustaremos:
- El código del monitor maestro
- Los límites de batch_size
- La estrategia de optimización




