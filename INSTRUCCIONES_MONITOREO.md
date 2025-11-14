# 🔍 INSTRUCCIONES DE MONITOREO

## Estado Actual

✅ **HAY 3 PROCESOS DE INGESTA ACTIVOS**

- PID 13128: Activo hace 1h 6m (CPU: 109%, RAM: 1.8 GB)
- PID 25216: Activo hace 1h 6m (CPU: 94%, RAM: 1.2 GB)  
- PID 33040: Activo hace 57m (CPU: 94%, RAM: 1.6 GB)

Todos están ejecutando `ingest_parallel_tier3.py` y están usando CPU activamente.

---

## 🚀 Monitoreo Automático

### Opción 1: Monitor Final (Recomendado)

```bash
python monitor_final.py
```

**Características**:
- ✅ Verifica cada 30 segundos
- ✅ Muestra progreso en tiempo real
- ✅ Notifica cuando termine (sonido + mensaje)
- ✅ No detiene la ingesta si lo cancelas
- ✅ Obtiene estadísticas cada 2 minutos (para no sobrecargar)

### Opción 2: Monitor Simple

```bash
python monitor_ingesta_simple.py
```

**Características**:
- ✅ Versión más ligera
- ✅ Verifica cada 30 segundos
- ✅ Notifica cuando termine

### Opción 3: Verificación Rápida

```bash
python verificar_estado_ingesta.py
```

**Características**:
- ✅ Verificación instantánea
- ✅ Muestra estado actual
- ✅ No monitorea continuamente

---

## 📊 Qué Monitorea

1. **Procesos Activos**: Detecta si hay procesos de ingesta corriendo
2. **Progreso**: Archivos indexados y chunks totales
3. **Recursos**: CPU y RAM de cada proceso
4. **Tiempo**: Tiempo activo de cada proceso

---

## 🔔 Notificación cuando Termine

El monitor detectará que la ingesta terminó cuando:
1. ❌ No hay procesos de ingesta activos
2. ⏸️ No hay cambios en las estadísticas por 5 minutos

Cuando termine, el monitor:
- ✅ Mostrará un mensaje grande de "INGESTA TERMINADA"
- ✅ Reproducirá un sonido (beep en Windows)
- ✅ Mostrará estadísticas finales

---

## ⚠️ Notas Importantes

1. **No detiene la ingesta**: Si cancelas el monitor (Ctrl+C), la ingesta continuará
2. **Timeouts**: Si la base de datos está muy cargada, puede haber timeouts al obtener estadísticas
3. **Múltiples procesos**: Es normal tener múltiples procesos si usas workers paralelos
4. **CPU alto**: Es normal que los procesos usen mucha CPU cuando están procesando activamente

---

## 🛠️ Solución de Problemas

### Si el monitor no detecta procesos:
- Verifica que los procesos estén corriendo: `python verificar_estado_ingesta.py`
- Los procesos pueden estar en diferentes scripts (ingest_parallel_tier3.py, ingest_optimized_rag.py, etc.)

### Si no puede obtener estadísticas:
- La base de datos puede estar muy cargada
- El monitor seguirá funcionando, solo no mostrará estadísticas
- Los procesos seguirán corriendo normalmente

### Si quieres detener la ingesta:
- **NO** canceles el monitor (solo detiene el monitoreo)
- Busca los procesos: `tasklist | findstr python`
- Detén los procesos manualmente si es necesario

---

## 📝 Estado Actual del Monitor

✅ **Monitor Final corriendo en background**

El monitor está verificando continuamente y te notificará cuando termine.

Para ver el estado en tiempo real, ejecuta:
```bash
python verificar_estado_ingesta.py
```

---

## 🎯 Próximos Pasos

1. ✅ Monitor corriendo en background
2. ⏳ Esperando a que termine la ingesta
3. 🔔 Se notificará automáticamente cuando termine
4. 📊 Se mostrarán estadísticas finales

**¡El monitor está activo y te notificará cuando termine!** 🚀



