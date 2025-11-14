# 📊 GUÍA DE MONITOREO EN VIVO

## 🚀 Script Principal de Monitoreo

### `monitor_y_ajustar_workers.py`

**Este es el script de monitoreo en vivo que:**
- ✅ Monitorea el progreso cada 30 segundos
- ✅ Ajusta workers automáticamente según velocidad
- ✅ Reinicia proceso si se detiene
- ✅ Muestra estadísticas en tiempo real

**Cómo ejecutarlo:**
```bash
python monitor_y_ajustar_workers.py
```

**Características:**
- Verifica progreso cada 30 segundos
- Calcula velocidad (archivos/minuto)
- Ajusta workers automáticamente para mantener ~70% de capacidad
- Muestra ETA (tiempo estimado de finalización)
- Reinicia proceso si se detiene (con cooldown de 1 minuto)

---

## 📊 Script de Verificación Rápida

### `check_progress_now.py`

**Para ver el estado actual rápidamente:**
```bash
python check_progress_now.py
```

**Muestra:**
- Procesos activos
- Configuración (batch_size)
- Progreso (archivos indexados/total)
- Barra de progreso visual

---

## 🔍 Script de Verificación Completa

### `verificar_todo.py`

**Para ver todos los procesos del sistema:**
```bash
python verificar_todo.py
```

**Muestra:**
- Procesos de ingestión activos
- Monitor inteligente activo
- Memoria y CPU de cada proceso

---

## 📈 Scripts Adicionales

### `verificar_proceso_paralelo.py`
Verifica específicamente procesos de ingestión paralela:
```bash
python verificar_proceso_paralelo.py
```

### `calcular_velocidad_real.py`
Calcula velocidad y proyección:
```bash
python calcular_velocidad_real.py
```

---

## 💡 RECOMENDACIÓN

**Para monitoreo continuo:**
```bash
python monitor_y_ajustar_workers.py
```

Este script se ejecuta indefinidamente y:
- Monitorea automáticamente
- Ajusta workers según necesidad
- Reinicia procesos si es necesario
- Muestra estadísticas en tiempo real

**Para verificación rápida:**
```bash
python check_progress_now.py
```

Útil para ver el estado actual sin ejecutar un monitor continuo.

---

## 🎯 Ejemplo de Salida del Monitor

```
================================================================================
🧠 MONITOR INTELIGENTE CON AJUSTE AUTOMÁTICO DE WORKERS
================================================================================

📊 ESTADO: 13:25:41
================================================================================
Archivos indexados: 610/1218 (50.08%)
Pendientes: 608
Procesos activos: 3
Workers configurados: 15
Velocidad: 25.50 archivos/minuto
ETA: 24 minutos

⏳ Próxima verificación en 30 segundos...
```

---

## ⚙️ Configuración del Monitor

El monitor verifica cada **30 segundos** por defecto.

Puedes ajustar el intervalo editando `monitor_y_ajustar_workers.py`:
```python
check_interval = 30  # Cambiar a 60 para verificar cada minuto
```

---

## 🛑 Detener el Monitor

Presiona `Ctrl+C` para detener el monitor.



