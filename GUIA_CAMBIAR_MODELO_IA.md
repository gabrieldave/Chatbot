# Guía para Cambiar el Modelo de IA

El sistema usa **LiteLLM**, que soporta múltiples proveedores de IA. Puedes cambiar fácilmente el modelo usando variables de entorno.

## Método 1: Usar Variable de Entorno CHAT_MODEL (Recomendado)

### Paso 1: Edita tu archivo `.env` en el directorio `backend`

Agrega o modifica la línea `CHAT_MODEL`:

```env
CHAT_MODEL=nombre_del_modelo
```

### Paso 2: Configura la API Key correspondiente

Dependiendo del modelo que elijas, necesitarás configurar su API key:

#### Para OpenAI (GPT-3.5, GPT-4, etc.):
```env
CHAT_MODEL=gpt-3.5-turbo
# o
CHAT_MODEL=gpt-4
# o
CHAT_MODEL=gpt-4-turbo-preview

OPENAI_API_KEY=tu_api_key_de_openai
```

#### Para Anthropic (Claude):
```env
CHAT_MODEL=claude-3-opus-20240229
# o
CHAT_MODEL=claude-3-sonnet-20240229
# o
CHAT_MODEL=claude-3-haiku-20240307

ANTHROPIC_API_KEY=tu_api_key_de_anthropic
```

#### Para Google (Gemini):
```env
CHAT_MODEL=gemini/gemini-pro
# o
CHAT_MODEL=gemini/gemini-1.5-pro

GOOGLE_API_KEY=tu_api_key_de_google
```

#### Para Deepseek (actual):
```env
CHAT_MODEL=deepseek-chat
DEEPSEEK_API_KEY=tu_api_key_de_deepseek
```

#### Para otros modelos soportados por LiteLLM:
- **Cohere**: `command`, `command-light`, `command-nightly`
- **Hugging Face**: `huggingface/nombre-del-modelo`
- **Replicate**: `replicate/nombre-del-modelo`
- **Azure OpenAI**: `azure/gpt-3.5-turbo`
- Y muchos más...

### Paso 3: Reinicia el backend

Después de cambiar el `.env`, reinicia el servidor:

```bash
# Detén el servidor (Ctrl+C)
# Luego inicia de nuevo:
python main.py
```

## Método 2: Modificar el Código Directamente

Si prefieres cambiar el código fuente, edita `main.py`:

### Ubicación: Líneas 49-67

Puedes modificar la lógica de selección del modelo. Por ejemplo, para usar OpenAI por defecto:

```python
# Cambiar esta sección:
if DEEPSEEK_API_KEY:
    modelo_por_defecto = "deepseek-chat"
else:
    modelo_por_defecto = "gpt-3.5-turbo"
```

A:

```python
# Para usar OpenAI siempre:
if OPENAI_API_KEY:
    modelo_por_defecto = "gpt-4"
else:
    modelo_por_defecto = "gpt-3.5-turbo"
```

## Modelos Recomendados por Proveedor

### OpenAI
- `gpt-3.5-turbo` - Rápido y económico
- `gpt-4` - Más potente, más caro
- `gpt-4-turbo-preview` - Última versión de GPT-4
- `gpt-4o` - Modelo optimizado

### Anthropic (Claude)
- `claude-3-haiku-20240307` - Rápido y económico
- `claude-3-sonnet-20240229` - Balance precio/rendimiento
- `claude-3-opus-20240229` - Más potente

### Google (Gemini)
- `gemini/gemini-pro` - Modelo estándar
- `gemini/gemini-1.5-pro` - Versión mejorada

### Deepseek
- `deepseek-chat` - Modelo actual
- `deepseek-coder` - Especializado en código

## Verificar que Funciona

Al iniciar el backend, deberías ver en la consola:

```
============================================================
Iniciando motor del chat...
Modelo de IA configurado: nombre-del-modelo
============================================================
```

## Notas Importantes

1. **API Keys**: Asegúrate de tener la API key correcta configurada para el modelo que elijas
2. **Costos**: Diferentes modelos tienen diferentes costos por token
3. **Límites**: Algunos proveedores tienen límites de rate limiting
4. **LiteLLM**: Consulta la documentación de LiteLLM para ver todos los modelos soportados: https://docs.litellm.ai/docs/providers

## Ejemplo Completo: Cambiar a GPT-4

1. Edita `backend/.env`:
```env
CHAT_MODEL=gpt-4
OPENAI_API_KEY=sk-tu-api-key-aqui
```

2. Reinicia el backend

3. Verifica en los logs que dice: `Modelo de IA configurado: gpt-4`

¡Listo! Ahora estás usando GPT-4.



