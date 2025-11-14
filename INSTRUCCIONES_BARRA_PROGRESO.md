# 📊 BARRA DE PROGRESO DE INGESTA

## 🚀 Cómo Ver la Barra de Progreso

### Opción 1: Barra de Progreso Visual (Recomendado)

```bash
python barra_progreso_ingesta.py
```

**Características**:
- ✅ Barra de progreso visual en tiempo real
- ✅ Actualización cada 2-5 segundos
- ✅ Muestra:
  - Chunks indexados
  - Archivos estimados
  - Velocidad (chunks/min, archivos/min)
  - Tiempo transcurrido
  - Estado del proceso
  - CPU y RAM del proceso

### Opción 2: Monitor Simple

```bash
python monitor_ingesta_simple.py
```

### Opción 3: Verificación Rápida

```bash
python verificar_estado_ingesta.py
```

---

## 📊 Qué Muestra la Barra de Progreso

### Con Rich (si está instalado):
- Tabla bonita con todas las métricas
- Barra de progreso visual
- Colores y formato mejorado
- Actualización en tiempo real

### Sin Rich:
- Barra de progreso ASCII
- Métricas en texto
- Actualización cada 5 segundos

---

## 🎯 Métricas Mostradas

1. **Chunks Indexados**: Total y incremento desde última verificación
2. **Archivos Estimados**: Basado en promedio de 100 chunks/archivo
3. **Velocidad**: Chunks por minuto y archivos por minuto
4. **Tiempo Transcurrido**: Horas, minutos, segundos
5. **Estado del Proceso**: Activo o pausado
6. **Recursos**: CPU y RAM del proceso

---

## 💡 Instalar Rich (Opcional pero Recomendado)

Para una barra de progreso más bonita:

```bash
pip install rich
```

---

## 🔄 Actualización Automática

La barra se actualiza automáticamente cada 2-5 segundos.

**Presiona Ctrl+C** para detener el monitor (no detiene la ingesta).

---

## 📝 Notas

- La barra muestra progreso basado en chunks indexados
- El total de archivos es una estimación
- Si hay timeout, la barra seguirá funcionando pero puede no mostrar conteo exacto
- El proceso de ingesta continúa independientemente del monitor

---

**✅ Ejecuta `python barra_progreso_ingesta.py` para ver el progreso en tiempo real!**



