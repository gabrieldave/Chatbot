# 🔬 GUÍA DEL EXPERIMENTO: Optimización de Batch Size

## 🎯 Objetivo

Optimizar el batch_size para futuros trabajos basándonos en datos reales de Supabase.

## 📋 Proceso del Experimento

### Paso 1: Estado Inicial (2 GB RAM)
1. Ejecuta: `python calculate_optimal_batch.py`
2. Proporciona los datos actuales de Supabase:
   - RAM Total: 2 GB
   - RAM Usada: (lo que veas en el panel)
   - batch_size actual: 15
3. Anota el batch_size recomendado

### Paso 2: Aumentar RAM a 4 GB
1. Ve al panel de Supabase
2. Aumenta Compute de 2 GB a 4 GB
3. Espera a que se reinicie (puede tardar unos minutos)

### Paso 3: Observar Cambios
1. Espera 5-10 minutos después del reinicio
2. Observa el uso de RAM en el panel de Supabase
3. Ejecuta: `python calculate_optimal_batch.py`
4. Proporciona los nuevos datos:
   - RAM Total: 4 GB
   - RAM Usada: (lo que veas ahora)
   - batch_size actual: 15 (se mantiene igual)
5. Anota el nuevo batch_size recomendado

### Paso 4: Análisis
**Si el uso de RAM aumentó (ej: de 1.8 GB a 3.6 GB):**
- ✅ Confirma que el margen de seguridad era REAL
- El batch_size puede aumentar proporcionalmente
- Con 4 GB, podemos usar batch_size más alto

**Si el uso de RAM se mantuvo (ej: sigue en 1.8 GB):**
- ✅ Confirma que había más capacidad disponible
- El límite era más conservador de lo necesario
- Podemos ser más agresivos incluso con 2 GB

## 🧮 Cálculo de Batch Size

El script `calculate_optimal_batch.py` calcula automáticamente basándose en:

1. **RAM Total**: Cuánta RAM tiene Supabase
2. **RAM Usada**: Cuánta está usando actualmente
3. **Margen de Seguridad**: 10% típico (200 MB en 2 GB, 400 MB en 4 GB)
4. **Factor de Seguridad**: 85% del RAM efectivamente disponible
5. **Capacidad por Archivo**: ~25 MB por archivo en memoria

### Fórmula:
```
RAM Segura = (RAM Total - Margen 10%) × 0.85
Batch Size = (RAM Segura en MB) / 25 MB por archivo
```

## 📊 Ejemplo de Cálculo

### Con 2 GB RAM, 1.8 GB usado:
- RAM Total: 2 GB
- Margen (10%): 0.2 GB
- RAM Efectiva: 1.8 GB
- RAM Segura (85%): 1.53 GB = 1,567 MB
- Batch Size: 1,567 / 25 = **~62 archivos**

### Con 4 GB RAM, 3.6 GB usado:
- RAM Total: 4 GB
- Margen (10%): 0.4 GB
- RAM Efectiva: 3.6 GB
- RAM Segura (85%): 3.06 GB = 3,133 MB
- Batch Size: 3,133 / 25 = **~125 archivos**

## 🔧 Aplicar Batch Size

Una vez calculado el batch_size óptimo:

```bash
python update_batch_size.py <nuevo_batch_size>
```

Ejemplo:
```bash
python update_batch_size.py 30
```

## 📝 Notas Importantes

- El batch_size actual está **FIJO en 15** para el experimento
- No ejecutes ingest_improved.py hasta terminar el experimento
- El monitor maestro está detenido para no interferir
- Después del experimento, ajustaremos todo según resultados

## 🎯 Resultado Esperado

Al final del experimento tendremos:
- ✅ Confirmación de si el margen de seguridad es real
- ✅ Batch_size óptimo para 2 GB RAM
- ✅ Batch_size óptimo para 4 GB RAM
- ✅ Estrategia de optimización para futuros trabajos




