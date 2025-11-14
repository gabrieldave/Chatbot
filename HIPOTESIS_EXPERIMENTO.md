# 🔬 HIPÓTESIS DEL EXPERIMENTO

## 📋 Situación Actual

- **batch_size**: 15 archivos
- **RAM Supabase**: 2 GB total
- **RAM Usada**: ~1.8 GB (90%)
- **RAM "Libre"**: ~200 MB (10%)

## 🎯 Hipótesis

**Supabase está reteniendo ~200 MB (10%) como margen de seguridad intencional.**

## 🔬 Experimento

### Configuración:
- **Mantener batch_size = 15** (NO cambiar nada)
- **Aumentar RAM de 2 GB a 4 GB** en Supabase
- **Observar qué pasa con el uso de RAM**

### Escenarios Posibles:

#### ✅ ESCENARIO A: Margen de Seguridad REAL (Hipótesis)
**Si el uso de RAM aumenta proporcionalmente:**
- De 1.8 GB (90% de 2 GB) → a ~3.6 GB (90% de 4 GB)
- **Conclusión**: Supabase SÍ está reteniendo RAM por seguridad
- **Implicación**: Debemos respetar el margen y cuidar el batch_size
- **Acción**: Calcular batch_size considerando el margen de seguridad

#### ❌ ESCENARIO B: Margen NO Real
**Si el uso de RAM se mantiene igual:**
- Se mantiene en ~1.8 GB (aunque ahora hay 4 GB disponibles)
- **Conclusión**: NO había límite real, había más capacidad disponible
- **Implicación**: Podemos ser más agresivos con el batch_size
- **Acción**: Aumentar batch_size aprovechando la capacidad extra

## 📊 Cálculo Esperado

### Si ESCENARIO A (Margen Real):
Con batch_size = 15:
- **Antes (2 GB)**: 1.8 GB usado = 90%
- **Después (4 GB)**: ~3.6 GB usado = 90%
- **Ratio**: 1.8 GB / 15 archivos = 0.12 GB por archivo
- **Con 4 GB disponible (3.6 GB efectivo)**: 3.6 / 0.12 = **~30 archivos por lote**

### Si ESCENARIO B (Margen NO Real):
Con batch_size = 15:
- **Antes (2 GB)**: 1.8 GB usado
- **Después (4 GB)**: Se mantiene en ~1.8 GB
- **Conclusión**: El proceso solo necesita 1.8 GB, no está limitado
- **Con 4 GB disponible**: Podríamos usar batch_size mucho mayor

## 🎯 Objetivo del Experimento

**Confirmar si debemos respetar el margen de seguridad o podemos ser más agresivos.**

## ✅ Estoy de Acuerdo

Sí, esta hipótesis tiene mucho sentido:
- Si el uso sube proporcionalmente → Confirma retención intencional
- Si el uso se mantiene → Indica que había más capacidad
- El batch_size constante (15) es la variable de control perfecta




