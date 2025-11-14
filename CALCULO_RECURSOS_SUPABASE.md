# 📊 Cálculo de Batch Size para Recursos de Supabase

## Recursos Disponibles

**Instancia MICRO de Supabase:**
- **RAM**: 1 GB
- **CPU**: 2-core ARM
- **Costo**: $0.01344 / hora

## Cálculo de Batch Size Óptimo

### Factores a Considerar

1. **RAM del Servidor (1 GB)**
   - Cada archivo procesado genera embeddings que se envían al servidor
   - Los embeddings se almacenan en la base de datos vectorial
   - Con 1 GB de RAM, el servidor puede manejar ~30-50 archivos por lote de forma segura

2. **CPU del Servidor (2-core ARM)**
   - Procesamiento de consultas SQL
   - Operaciones de inserción en la base de datos
   - ARM es eficiente pero menos potente que x86

3. **RAM Local (32 GB disponible)**
   - Podemos procesar más archivos localmente
   - Pero el servidor es el cuello de botella
   - Necesitamos balancear procesamiento local vs carga del servidor

### Batch Size Recomendado

**Rango Seguro:**
- **Mínimo**: 10 archivos por lote (muy seguro, no sobrecarga)
- **Óptimo inicial**: 15-20 archivos por lote
- **Máximo seguro**: 30-50 archivos por lote (depende del tamaño de los archivos)

**Estrategia de Ajuste:**
- Empezar con 10-15 archivos
- Si hay progreso constante y sin errores, aumentar gradualmente (+5 cada vez)
- Si hay timeouts o errores, reducir (-5 cada vez)
- No exceder 50 archivos por lote con estos recursos

### Estimación de Tiempo

Con batch_size de 20 archivos:
- **Velocidad estimada**: ~0.1-0.2 archivos/segundo
- **Tiempo por lote**: ~2-3 minutos
- **Total para 1,218 archivos**: ~60-70 lotes = ~2-3.5 horas

Con batch_size de 30 archivos:
- **Velocidad estimada**: ~0.15-0.25 archivos/segundo
- **Tiempo por lote**: ~2-4 minutos
- **Total para 1,218 archivos**: ~40-50 lotes = ~1.5-3 horas

### Recomendaciones

1. **Empezar conservadoramente**: batch_size = 15
2. **Monitorear**: Usar `master_monitor.py` para ajuste automático
3. **Aumentar gradualmente**: Solo si hay progreso constante sin errores
4. **No exceder 50**: El servidor tiene límites físicos con 1 GB RAM

### Notas Importantes

- El proceso local puede manejar más, pero el servidor es el límite
- Los timeouts indican que el servidor está sobrecargado
- Es mejor ir lento y constante que rápido y con errores
- El monitor automático ajustará según el progreso real




