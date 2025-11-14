# 💰 REDUCCIÓN DE COSTOS - DEEPSEEK vs OPENAI

## ✅ Configuración Actual para Ahorrar

### Chat (Respuestas) - DeepSeek ✅
- **Modelo**: `deepseek-chat`
- **Costo**: ~$0.14 por 1M tokens entrada, ~$0.28 por 1M tokens salida
- **Estado**: Configurado y funcionando ✅

### Embeddings (Búsqueda RAG) - OpenAI (Necesario)
- **Modelo**: `text-embedding-3-small`
- **Costo**: ~$0.02 por 1M tokens
- **Estado**: Necesario para el RAG (no se puede cambiar fácilmente)

---

## 📊 Comparación de Costos

### Escenario: 1000 consultas con 500 tokens de salida cada una

| Componente | Modelo | Tokens | Costo |
|------------|--------|--------|-------|
| **Chat (Respuestas)** | DeepSeek | 500K | **$0.14** |
| **Chat (Respuestas)** | GPT-3.5 | 500K | **$0.75** |
| **Chat (Respuestas)** | GPT-4 | 500K | **$15.00** |
| **Embeddings** | OpenAI | 100K | **$0.002** |

**Ahorro con DeepSeek**: 
- vs GPT-3.5: **~81% más barato**
- vs GPT-4: **~99% más barato**

---

## ✅ Verificación

El código ahora:
1. ✅ **Respeta CHAT_MODEL** si está configurado (usa DeepSeek)
2. ✅ **Prioriza DeepSeek** si no hay CHAT_MODEL
3. ✅ **NO cambia automáticamente** a OpenAI

---

## 🔍 Cómo Verificar que Está Usando DeepSeek

### En los logs del backend deberías ver:
```
✓ Modelo configurado manualmente en CHAT_MODEL: deepseek-chat
✓ API Key de Deepseek configurada
Modelo de IA configurado: deepseek-chat
```

### En cada consulta deberías ver:
```
📤 Enviando consulta a deepseek-chat (query: ...)
✓ Respuesta recibida de deepseek-chat
```

---

## ⚠️ Nota sobre Embeddings

Los **embeddings** (para búsqueda RAG) usan OpenAI `text-embedding-3-small` porque:
- Es necesario para el sistema RAG
- Es MUY barato ($0.02 por 1M tokens)
- Solo se usa para buscar contexto, no para generar respuestas

**El costo de embeddings es mínimo comparado con el chat.**

---

## 💡 Recomendación

**Para maximizar el ahorro:**
1. ✅ Mantén `CHAT_MODEL=deepseek-chat` en tu `.env`
2. ✅ El sistema usará DeepSeek para todas las respuestas
3. ✅ Los embeddings seguirán usando OpenAI (necesario y barato)

---

## 🧪 Prueba de Costos

Después de hacer algunas consultas, puedes verificar:
- Los logs mostrarán qué modelo se usó
- DeepSeek es ~5x más barato que GPT-3.5
- DeepSeek es ~100x más barato que GPT-4

---

**✅ Con la configuración actual, estás usando DeepSeek y ahorrando significativamente en costos!**



