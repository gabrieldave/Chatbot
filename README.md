# 🤖 Chatbot RAG con Sistema de Plantilla Configurable

Un sistema completo de chatbot RAG (Retrieval Augmented Generation) construido con FastAPI, LlamaIndex y Supabase. Este proyecto está diseñado como **plantilla reutilizable** para crear chatbots especializados en cualquier dominio (trading, cocina, psicología, medicina, etc.).

## ✨ Características

- ✅ **Sistema RAG completo** con indexación de documentos (PDF, EPUB, TXT, DOCX)
- ✅ **Plantilla configurable** - Cambia de dominio en minutos editando `config.py`
- ✅ **Sistema de tokens** para control de uso y monetización
- ✅ **Autenticación** con Supabase Auth
- ✅ **Historial de conversaciones** persistente
- ✅ **Soporte múltiples modelos de IA** (OpenAI, Deepseek, Claude, Gemini, etc.)
- ✅ **API REST** con FastAPI y documentación automática
- ✅ **Detección automática** de archivos ya indexados

## 🚀 Inicio Rápido

### 1. Clonar el Repositorio

```bash
git clone https://github.com/gabrieldave/Chatbot.git
cd Chatbot
```

### 2. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar Variables de Entorno

Copia `env.example.txt` a `.env` y completa con tus credenciales:

```bash
cp env.example.txt .env
```

Edita `.env` con:
- Credenciales de Supabase (URL, Service Key, DB Password)
- API Keys de modelos de IA (OpenAI, Deepseek, etc.)

### 4. Configurar Supabase

Ejecuta estos scripts SQL en el SQL Editor de Supabase:

1. `create_profiles_table.sql` - Crea tabla de perfiles con sistema de tokens
2. `create_conversations_table.sql` - Crea tabla de historial de conversaciones

### 5. Configurar el Dominio (Opcional)

Edita `config.py` para personalizar según tu dominio:

```python
DOMAIN_NAME = "trading"  # Cambia a "cocina", "psicologia", etc.
ASSISTANT_DESCRIPTION = "Eres un asistente experto en trading..."
```

### 6. Agregar Documentos

Coloca tus documentos (PDFs, EPUBs, etc.) en la carpeta `./data`

### 7. Indexar Documentos

```bash
python ingest_improved.py
```

### 8. Iniciar el Servidor

```bash
python main.py
```

El servidor estará disponible en `http://localhost:8000`

## 📚 Documentación

- **[README_PLANTILLA.md](README_PLANTILLA.md)** - Guía completa para usar como plantilla
- **[QUICK_START_PLANTILLA.md](QUICK_START_PLANTILLA.md)** - Inicio rápido para nuevos proyectos
- **[GUIA_CAMBIAR_MODELO_IA.md](GUIA_CAMBIAR_MODELO_IA.md)** - Cómo cambiar el modelo de IA

## 🎯 Uso como Plantilla

Este proyecto está diseñado para ser reutilizado fácilmente. Para crear un nuevo chatbot:

### Opción 1: Script Automático

```bash
python setup_nuevo_proyecto.py
```

### Opción 2: Manual

1. Copia el proyecto a una nueva carpeta
2. Edita `config.py` con tu dominio
3. Configura `.env` con tus credenciales
4. Agrega tus documentos a `./data`
5. Ejecuta `python ingest_improved.py`

## 📁 Estructura del Proyecto

```
backend/
├── config.py                    # ⭐ Configuración del dominio (edita esto)
├── main.py                      # Servidor FastAPI
├── ingest.py                    # Script de ingestión básico
├── ingest_improved.py           # Script de ingestión mejorado (recomendado)
├── setup_nuevo_proyecto.py      # Script de configuración automática
├── requirements.txt             # Dependencias Python
├── .env                         # Variables de entorno (NO subir a git)
├── env.example.txt              # Plantilla de variables de entorno
├── data/                        # 📁 Coloca tus documentos aquí (excluido de git)
├── create_profiles_table.sql    # Script SQL para tabla de perfiles
├── create_conversations_table.sql # Script SQL para tabla de conversaciones
├── README.md                    # Este archivo
├── README_PLANTILLA.md          # Guía completa de plantilla
├── QUICK_START_PLANTILLA.md     # Inicio rápido
└── GUIA_CAMBIAR_MODELO_IA.md    # Guía para cambiar modelo de IA
```

## 🔧 Configuración

### Variables de Entorno Requeridas

```env
SUPABASE_URL=https://tuproyecto.supabase.co
SUPABASE_SERVICE_KEY=tu_service_key
SUPABASE_DB_PASSWORD=tu_contraseña_db
OPENAI_API_KEY=sk-tu_api_key  # Al menos una API key es requerida
```

### Variables Opcionales

```env
CHAT_MODEL=gpt-3.5-turbo  # Modelo específico (opcional)
DEEPSEEK_API_KEY=tu_key
ANTHROPIC_API_KEY=tu_key
GOOGLE_API_KEY=tu_key
COHERE_API_KEY=tu_key
```

## 🎨 Ejemplos de Configuración

### Para Trading (actual)
```python
DOMAIN_NAME = "trading"
ASSISTANT_DESCRIPTION = "Eres un asistente experto en trading y psicología del trading..."
```

### Para Cocina
```python
DOMAIN_NAME = "cocina"
ASSISTANT_DESCRIPTION = "Eres un asistente experto en cocina, recetas y técnicas culinarias..."
```

### Para Psicología
```python
DOMAIN_NAME = "psicologia"
ASSISTANT_DESCRIPTION = "Eres un asistente experto en psicología y salud mental..."
```

## 📡 API Endpoints

- `POST /chat` - Enviar mensaje al chatbot (requiere autenticación)
- `GET /tokens` - Consultar tokens restantes (requiere autenticación)
- `POST /tokens/reload` - Recargar tokens (requiere autenticación)
- `GET /conversations` - Obtener historial (requiere autenticación)
- `GET /health` - Verificar estado del servidor
- `GET /docs` - Documentación interactiva de la API

## 🔐 Autenticación

El sistema usa autenticación JWT de Supabase. Todas las peticiones (excepto `/health` y `/docs`) requieren un header:

```
Authorization: Bearer <token_jwt>
```

## 💡 Características Avanzadas

- **Detección de duplicados**: El script `ingest_improved.py` detecta automáticamente archivos ya indexados
- **Procesamiento en lotes**: Indexa documentos en lotes para mejor rendimiento
- **Sistema de tokens**: Control de uso con descuento automático
- **Historial persistente**: Todas las conversaciones se guardan en Supabase
- **Múltiples modelos**: Soporte para OpenAI, Deepseek, Claude, Gemini, Cohere y más

## 🛠️ Tecnologías Utilizadas

- **FastAPI** - Framework web moderno y rápido
- **LlamaIndex** - Framework para aplicaciones RAG
- **Supabase** - Backend como servicio (PostgreSQL + Auth)
- **LiteLLM** - Abstracción para múltiples proveedores de IA
- **OpenAI Embeddings** - Para generar embeddings de documentos

## 📝 Notas Importantes

- ⚠️ La carpeta `data/` está excluida del repositorio (`.gitignore`)
- ⚠️ Nunca subas el archivo `.env` al repositorio
- ✅ Los documentos deben estar en formato: PDF, EPUB, TXT, DOCX, MD
- ✅ El sistema detecta automáticamente qué modelo usar según las API keys disponibles

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está disponible para uso personal y comercial.

## 🆘 Soporte

Si tienes problemas:

1. Revisa la documentación en `README_PLANTILLA.md`
2. Verifica que todas las variables de entorno estén configuradas
3. Asegúrate de que los scripts SQL se hayan ejecutado en Supabase
4. Verifica los logs del servidor para errores

## 🎉 ¡Listo para Usar!

Este proyecto está diseñado para ser una plantilla completa y reutilizable. Solo necesitas:

1. ✅ Configurar `config.py` con tu dominio
2. ✅ Agregar tus documentos a `./data`
3. ✅ Ejecutar `ingest_improved.py`
4. ✅ Iniciar el servidor con `python main.py`

¡Feliz desarrollo! 🚀

