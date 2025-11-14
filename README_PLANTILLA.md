# 🚀 Guía: Cómo Usar Este Proyecto como Plantilla

Esta guía te explica cómo reutilizar este código base para crear chatbots RAG (Retrieval Augmented Generation) para diferentes dominios/temas.

## 📋 Tabla de Contenidos

1. [¿Qué es una Plantilla?](#qué-es-una-plantilla)
2. [Pasos para Crear un Nuevo Proyecto](#pasos-para-crear-un-nuevo-proyecto)
3. [Configuración del Dominio](#configuración-del-dominio)
4. [Ejemplos de Configuración](#ejemplos-de-configuración)
5. [Estructura del Proyecto](#estructura-del-proyecto)
6. [Preguntas Frecuentes](#preguntas-frecuentes)

---

## ¿Qué es una Plantilla?

Una plantilla es un código base que puedes reutilizar para diferentes proyectos cambiando solo la configuración, sin modificar el código fuente. En este caso, puedes usar el mismo código para:

- ✅ **Trading** (proyecto actual)
- ✅ **Cocina** (recetas y técnicas culinarias)
- ✅ **Psicología** (libros y artículos de psicología)
- ✅ **Medicina** (documentos médicos)
- ✅ **Educación** (material educativo)
- ✅ **Cualquier otro dominio**

---

## Pasos para Crear un Nuevo Proyecto

### Paso 1: Copiar el Proyecto

```bash
# Opción A: Clonar el repositorio y crear una nueva rama/carpeta
cp -r MI_SAAS_BOT/backend MI_SAAS_BOT_COCINA/backend

# Opción B: Crear un nuevo proyecto desde cero y copiar los archivos necesarios
```

### Paso 2: Configurar el Dominio

Edita el archivo `config.py` y modifica las siguientes variables:

```python
# Ejemplo para un proyecto de COCINA:
DOMAIN_NAME = "cocina"
ASSISTANT_DESCRIPTION = "Eres un asistente experto en cocina, recetas y técnicas culinarias. Responde basándote en el contexto proporcionado."
API_TITLE = "Chat Bot API - Cocina"
API_DESCRIPTION = "API para consultar recetas y técnicas culinarias indexadas con sistema de tokens"
```

### Paso 3: Configurar Variables de Entorno

1. Copia el archivo `.env.example` a `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edita `.env` con tus credenciales de Supabase y API keys

### Paso 4: Configurar Supabase

1. Crea un nuevo proyecto en Supabase (o usa uno existente)
2. Ejecuta los scripts SQL para crear las tablas:
   ```bash
   # En el SQL Editor de Supabase, ejecuta:
   - create_profiles_table.sql
   - create_conversations_table.sql
   ```

### Paso 5: Agregar Documentos

1. Coloca tus documentos (PDFs, EPUBs, TXTs, etc.) en la carpeta `./data`
2. Ejecuta el script de ingestión:
   ```bash
   python ingest_improved.py
   ```

### Paso 6: Iniciar el Servidor

```bash
python main.py
```

¡Listo! Tu chatbot está funcionando con el nuevo dominio.

---

## Configuración del Dominio

El archivo `config.py` es el corazón de la personalización. Aquí están todas las opciones:

### Variables Principales

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `DOMAIN_NAME` | Nombre del dominio/tema | `"cocina"`, `"psicologia"`, `"trading"` |
| `ASSISTANT_DESCRIPTION` | Descripción del asistente (usado en el prompt) | `"Eres un asistente experto en..."` |
| `API_TITLE` | Título de la API | `"Chat Bot API - Cocina"` |
| `API_DESCRIPTION` | Descripción de la API | `"API para consultar recetas..."` |
| `VECTOR_COLLECTION_NAME` | Nombre de la colección en Supabase | `"knowledge"` (puede ser el mismo para todos) |
| `DATA_DIRECTORY` | Carpeta con los documentos | `"./data"` |

### Variables Avanzadas

| Variable | Descripción | Valor por Defecto |
|----------|-------------|-------------------|
| `SIMILARITY_TOP_K` | Número de documentos similares a recuperar | `5` |
| `MODEL_TEMPERATURE` | Creatividad del modelo (0.0-1.0) | `0.7` |
| `INITIAL_TOKENS` | Tokens iniciales para nuevos usuarios | `20000` |

---

## Ejemplos de Configuración

### Ejemplo 1: Proyecto de Cocina

```python
# config.py
DOMAIN_NAME = "cocina"
ASSISTANT_DESCRIPTION = "Eres un asistente experto en cocina, recetas y técnicas culinarias. Responde basándote en el contexto proporcionado."
API_TITLE = "Chat Bot API - Cocina"
API_DESCRIPTION = "API para consultar recetas y técnicas culinarias indexadas con sistema de tokens"
```

**Documentos a agregar:**
- Libros de recetas (PDFs)
- Guías de técnicas culinarias
- Artículos sobre gastronomía

### Ejemplo 2: Proyecto de Psicología

```python
# config.py
DOMAIN_NAME = "psicologia"
ASSISTANT_DESCRIPTION = "Eres un asistente experto en psicología y salud mental. Responde basándote en el contexto proporcionado."
API_TITLE = "Chat Bot API - Psicología"
API_DESCRIPTION = "API para consultar documentos sobre psicología indexados con sistema de tokens"
```

**Documentos a agregar:**
- Libros de psicología
- Artículos científicos
- Manuales de terapia

### Ejemplo 3: Proyecto de Medicina

```python
# config.py
DOMAIN_NAME = "medicina"
ASSISTANT_DESCRIPTION = "Eres un asistente experto en medicina y salud. Responde basándote en el contexto proporcionado. IMPORTANTE: Siempre recomienda consultar con un profesional médico para diagnósticos."
API_TITLE = "Chat Bot API - Medicina"
API_DESCRIPTION = "API para consultar documentos médicos indexados con sistema de tokens"
```

**Documentos a agregar:**
- Libros de medicina
- Guías clínicas
- Artículos médicos

---

## Estructura del Proyecto

```
backend/
├── config.py                    # ⭐ CONFIGURACIÓN DEL DOMINIO (edita esto)
├── main.py                      # Servidor FastAPI
├── ingest.py                    # Script de ingestión básico
├── ingest_improved.py           # Script de ingestión mejorado (recomendado)
├── requirements.txt             # Dependencias Python
├── .env                         # Variables de entorno (NO subir a git)
├── .env.example                 # Plantilla de variables de entorno
├── data/                        # 📁 Coloca tus documentos aquí
│   ├── libro1.pdf
│   ├── libro2.epub
│   └── ...
├── create_profiles_table.sql    # Script SQL para crear tabla de perfiles
├── create_conversations_table.sql # Script SQL para crear tabla de conversaciones
└── README_PLANTILLA.md          # Esta guía
```

---

## Preguntas Frecuentes

### ¿Puedo usar el mismo proyecto de Supabase para múltiples dominios?

**Sí**, pero con consideraciones:

- **Opción A**: Usar la misma colección (`VECTOR_COLLECTION_NAME = "knowledge"`)
  - ✅ Más simple
  - ⚠️ Todos los documentos se mezclan en la misma colección
  - ✅ Útil si los dominios son relacionados

- **Opción B**: Usar colecciones diferentes (`VECTOR_COLLECTION_NAME = "knowledge_cocina"`)
  - ✅ Separación completa de datos
  - ✅ Mejor organización
  - ⚠️ Requiere crear nuevas colecciones en Supabase

**Recomendación**: Usa colecciones diferentes si los dominios son completamente distintos.

### ¿Necesito crear un nuevo proyecto de Supabase para cada dominio?

**No necesariamente**. Puedes:

1. **Usar el mismo proyecto** con diferentes colecciones de vectores
2. **Crear proyectos separados** para mejor aislamiento

**Recomendación**: Para producción, usa proyectos separados. Para desarrollo/pruebas, puedes usar el mismo proyecto.

### ¿Cómo cambio el modelo de IA?

Edita el archivo `.env` y agrega:

```env
CHAT_MODEL=gpt-4
OPENAI_API_KEY=tu_api_key
```

O consulta `GUIA_CAMBIAR_MODELO_IA.md` para más detalles.

### ¿Puedo tener múltiples proyectos corriendo al mismo tiempo?

**Sí**, pero necesitas:

1. Diferentes puertos (el servidor busca automáticamente uno disponible)
2. Diferentes proyectos de Supabase (o diferentes colecciones)
3. Diferentes carpetas de proyecto

### ¿Qué formatos de documentos soporta?

- ✅ PDF (`.pdf`)
- ✅ EPUB (`.epub`)
- ✅ Texto plano (`.txt`)
- ✅ Word (`.docx`)
- ✅ Markdown (`.md`)

### ¿Cómo actualizo los documentos después de agregar nuevos?

Simplemente ejecuta `ingest_improved.py` de nuevo. El script detecta automáticamente qué archivos ya están indexados y solo procesa los nuevos.

---

## Checklist para Nuevo Proyecto

- [ ] Copiar proyecto base
- [ ] Editar `config.py` con el nuevo dominio
- [ ] Configurar `.env` con credenciales
- [ ] Crear/ejecutar scripts SQL en Supabase
- [ ] Agregar documentos a `./data`
- [ ] Ejecutar `ingest_improved.py`
- [ ] Probar el servidor con `python main.py`
- [ ] Verificar que responde correctamente

---

## Soporte

Si tienes problemas o preguntas:

1. Revisa los logs del servidor
2. Verifica que las variables de entorno estén correctas
3. Asegúrate de que los documentos se hayan indexado correctamente
4. Consulta la documentación de Supabase y LlamaIndex

---

## Conclusión

Con esta plantilla, puedes crear chatbots RAG para cualquier dominio en minutos. Solo necesitas:

1. ✅ Cambiar `config.py`
2. ✅ Agregar tus documentos
3. ✅ Configurar las variables de entorno

¡Feliz desarrollo! 🚀

