# 📊 GUÍA DE MONITOREO - BATCH_SIZE 150

## ✅ Cambios Aplicados

- **batch_size anterior**: 80 archivos
- **batch_size nuevo**: 150 archivos
- **Aumento**: +70 archivos (+87.5%)
- **Proceso reiniciado**: ✅

## 📊 Métricas a Monitorear

### 1. **CPU en Supabase**
- **Antes**: 6.49%
- **Esperado**: Debería aumentar pero mantenerse bajo (<30%)
- **Alerta**: Si supera 80%, reducir batch_size

### 2. **IOPS en Supabase**
- **Antes**: 0.04% (1.31 IOPS)
- **Esperado**: Debería aumentar pero mantenerse bajo (<10%)
- **Alerta**: Si supera 50%, puede haber cuello de botella

### 3. **RAM en Supabase**
- **Antes**: 7.5% usado (288 MB de 3.74 GB)
- **Esperado**: Debería aumentar proporcionalmente
- **Cálculo**: Con 150 archivos, esperamos ~540 MB (14.4%)
- **Alerta**: Si supera 80%, reducir batch_size

### 4. **Velocidad de Procesamiento**
- **Antes**: ~1,384 archivos/hora
- **Esperado**: ~1,989 archivos/hora (1.44x más rápido)
- **Cómo verificar**: Ejecutar `python calcular_velocidad_real.py`

## 🔍 Cómo Monitorear

### Opción 1: Panel de Supabase
1. Ve a tu proyecto en Supabase
2. Revisa las métricas de:
   - CPU Usage
   - Memory Usage
   - IOPS

### Opción 2: Scripts Locales
```bash
# Ver estado y progreso
python check_progress_now.py

# Calcular velocidad real
python calcular_velocidad_real.py

# Ver estado del sistema
python check_status.py
```

## ⏱️ Tiempo de Monitoreo

**Recomendado**: Monitorear durante los primeros 10-15 minutos para:
- Verificar que los recursos no se sobrecarguen
- Confirmar que la velocidad mejoró
- Detectar cualquier problema temprano

## ⚠️ Señales de Alerta

Si observas alguno de estos, **reducir batch_size**:
- CPU > 80%
- IOPS > 50%
- RAM > 80%
- Errores o timeouts frecuentes
- Velocidad no mejora o empeora

## ✅ Señales Positivas

Si observas estos, **el batch_size está bien**:
- CPU entre 20-50%
- IOPS < 20%
- RAM < 50%
- Velocidad mejoró significativamente
- Sin errores

## 📝 Próximos Pasos

1. **Monitorear** durante 10-15 minutos
2. **Verificar velocidad** con `python calcular_velocidad_real.py`
3. **Ajustar si es necesario** basado en las métricas

## 🎯 Objetivo

Aprovechar los recursos disponibles (CPU 93.5%, IOPS 99.96%, RAM 92.5%) para procesar más rápido sin sobrecargar el sistema.




